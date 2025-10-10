import os
import gc
import numpy as np
import pandas as pd
import xgboost as xgb
import time
import pickle
import tempfile
import mmap
from tqdm import tqdm
import polars as pl
from pathlib import Path


class LargeDataXGBoostTrainer:
    """
    用于处理超大规模数据集的XGBoost训练器
    支持外部内存模式、数据分批加载和增量训练
    适用于内存占用约800G的大规模数据集
    """
    
    def __init__(self, model_config, output_dir, temp_dir=None):
        """
        初始化训练器
        
        Args:
            model_config: 模型配置字典
            output_dir: 模型和中间文件输出目录
            temp_dir: 临时文件目录，默认使用系统临时目录
        """
        self.model_config = model_config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 临时目录用于存储中间文件
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "xgb_large_data"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化XGBoost参数
        self.xgb_params = model_config.get("xgb_config", {})
        # 设置外部内存模式
        self.xgb_params.update({
            'tree_method': 'hist',  # 使用直方图方法，内存效率更高
            'grow_policy': 'lossguide',  # 基于损失的分裂策略
            'max_bin': 256,  # 减少分箱数量以节省内存
            'predictor': 'cpu_predictor'  # 使用CPU预测器
        })
        
        self.model = None
        self.feature_names = None
        self.batch_size = 1000000  # 每批处理的样本数量
        
    def prepare_libsvm_file(self, symbol_list, data_config, output_file=None):
        """
        将数据转换为LibSVM格式文件，以减少内存占用
        
        Args:
            symbol_list: 股票代码列表
            data_config: 数据配置
            output_file: 输出文件路径，默认为临时目录中的文件
            
        Returns:
            生成的LibSVM文件路径
        """
        if output_file is None:
            output_file = self.temp_dir / "train_data.libsvm"
        
        # 使用with open确保文件正确关闭
        with open(output_file, 'w') as f_out:
            for symbol in tqdm(symbol_list, desc="准备LibSVM数据"):
                try:
                    # 读取因子数据和标签数据
                    factor_file = os.path.join(self.model_config["exp_path"], f"dataset/{symbol}_flying_factor.parquet")
                    label_file = os.path.join(self.model_config["exp_path"], f"dataset/{symbol}_flying_label.parquet")
                    
                    if not (os.path.exists(factor_file) and os.path.exists(label_file)):
                        print(f"无该标的因子数据：{symbol}")
                        continue
                    
                    # 使用polars进行高效数据处理
                    factor_df = pl.read_parquet(factor_file).filter(
                        (pl.col("DateTime") >= pl.lit(self.model_config["train_start_time"]).str.to_datetime("%Y%m%d")) &
                        (pl.col("DateTime") <= pl.lit(self.model_config["valid_end_time"]).str.to_datetime("%Y%m%d"))
                    ).filter(
                        ~pl.col("DateTime").dt.strftime("%Y%m%d").is_in(self.model_config.get("filter_time", []))
                    )
                    
                    label_df = pl.read_parquet(label_file).filter(
                        (pl.col("DateTime") >= pl.lit(self.model_config["train_start_time"]).str.to_datetime("%Y%m%d")) &
                        (pl.col("DateTime") <= pl.lit(self.model_config["valid_end_time"]).str.to_datetime("%Y%m%d"))
                    ).filter(
                        ~pl.col("DateTime").dt.strftime("%Y%m%d").is_in(self.model_config.get("filter_time", []))
                    )
                    
                    # 合并数据
                    merged_df = factor_df.join(label_df, on="DateTime")
                    
                    # 提取特征和标签
                    feature_cols = self.model_config["factor_name_list"]
                    label_col = self.model_config["tagger_name_list"][0] if self.model_config["tagger_name_list"] else None
                    
                    if not label_col:
                        print(f"警告：未指定标签列，跳过{symbol}")
                        continue
                    
                    # 转换为pandas以便处理
                    pd_df = merged_df.select(["DateTime"] + feature_cols + [label_col]).to_pandas()
                    
                    # 处理缺失值
                    pd_df = pd_df.dropna()
                    
                    # 限制样本数量以避免内存溢出
                    if len(pd_df) > self.batch_size:
                        pd_df = pd_df.sample(self.batch_size, random_state=42)
                    
                    # 将数据写入LibSVM格式文件
                    for _, row in pd_df.iterrows():
                        label = row[label_col]
                        features = [f"{i+1}:{row[col]}" for i, col in enumerate(feature_cols) if not pd.isna(row[col])]
                        if features:  # 确保有特征
                            f_out.write(f"{label} {' '.join(features)}\n")
                    
                    # 保存特征名称以便后续使用
                    if self.feature_names is None:
                        self.feature_names = feature_cols
                    
                except Exception as e:
                    print(f"处理{symbol}时出错: {e}")
        
        print(f"LibSVM数据准备完成，保存至: {output_file}")
        return output_file
    
    def train_with_external_memory(self, train_file, valid_file=None, early_stopping_rounds=10):
        """
        使用外部内存模式训练XGBoost模型
        
        Args:
            train_file: 训练数据文件路径（LibSVM格式）
            valid_file: 验证数据文件路径（LibSVM格式），可选
            early_stopping_rounds: 早停轮数
            
        Returns:
            训练好的XGBoost模型
        """
        print("使用外部内存模式训练XGBoost模型...")
        
        # 创建DMatrix，使用外部内存模式
        dtrain = xgb.DMatrix(f"libsvm:{train_file}?format=libsvm&cache_prefix={self.temp_dir}/train_cache")
        
        evals = [(dtrain, 'train')]
        if valid_file:
            dvalid = xgb.DMatrix(f"libsvm:{valid_file}?format=libsvm&cache_prefix={self.temp_dir}/valid_cache")
            evals.append((dvalid, 'valid'))
        
        # 设置训练参数
        num_boost_round = self.xgb_params.pop('n_estimators', 2000)
        self.xgb_params['verbosity'] = 1
        
        # 训练模型
        start_time = time.time()
        self.model = xgb.train(
            self.xgb_params,
            dtrain,
            num_boost_round=num_boost_round,
            evals=evals,
            early_stopping_rounds=early_stopping_rounds,
            verbose_eval=10
        )
        
        print(f"模型训练完成，耗时: {time.time() - start_time:.2f}秒")
        return self.model
    
    def train_with_batches(self, symbol_list, batch_size=None):
        """
        使用批处理方式训练模型，适用于数据无法一次性加载到内存的情况
        
        Args:
            symbol_list: 股票代码列表
            batch_size: 每批处理的股票数量，默认为10
            
        Returns:
            训练好的XGBoost模型
        """
        if batch_size is None:
            batch_size = 10  # 默认每批处理10个股票
        
        # 初始化模型
        self.model = None
        
        # 分批处理股票
        for i in range(0, len(symbol_list), batch_size):
            batch_symbols = symbol_list[i:i+batch_size]
            print(f"处理批次 {i//batch_size + 1}/{(len(symbol_list)-1)//batch_size + 1}, 股票: {batch_symbols}")
            
            # 为当前批次准备数据
            batch_train_file = self.temp_dir / f"batch_{i//batch_size}_train.libsvm"
            self.prepare_libsvm_file(batch_symbols, self.model_config, output_file=batch_train_file)
            
            # 训练或增量训练模型
            if self.model is None:
                # 首次训练
                self.train_with_external_memory(batch_train_file)
            else:
                # 增量训练
                dtrain = xgb.DMatrix(f"libsvm:{batch_train_file}?format=libsvm&cache_prefix={self.temp_dir}/batch_cache")
                self.model = xgb.train(
                    self.xgb_params,
                    dtrain,
                    num_boost_round=100,  # 增量训练使用较少的轮数
                    xgb_model=self.model  # 使用之前的模型继续训练
                )
            
            # 删除临时文件以释放空间
            if os.path.exists(batch_train_file):
                os.remove(batch_train_file)
            
            # 强制垃圾回收
            gc.collect()
        
        return self.model
    
    def save_model(self, model_path=None):
        """
        保存模型到文件
        
        Args:
            model_path: 模型保存路径，默认为output_dir/model.json
            
        Returns:
            保存的模型文件路径
        """
        if self.model is None:
            raise ValueError("模型尚未训练，无法保存")
        
        if model_path is None:
            model_path = self.output_dir / "model.json"
        
        # 保存为JSON格式，更小更快
        self.model.save_model(str(model_path))
        print(f"模型已保存至: {model_path}")
        
        # 同时保存为pickle格式以兼容现有代码
        pickle_path = self.output_dir / "tmp_model.pickle.dat"
        with open(pickle_path, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"模型pickle格式已保存至: {pickle_path}")
        
        # 保存特征名称
        if self.feature_names:
            feature_path = self.output_dir / "features.csv"
            with open(feature_path, 'w') as f:
                for feature in self.feature_names:
                    f.write(f"{feature},\n")
            print(f"特征名称已保存至: {feature_path}")
        
        return model_path
    
    def predict_with_memory_mapping(self, data_file, output_file=None):
        """
        使用内存映射技术进行大规模数据预测
        
        Args:
            data_file: 预测数据文件路径（LibSVM或CSV格式）
            output_file: 预测结果输出文件路径
            
        Returns:
            预测结果文件路径
        """
        if self.model is None:
            raise ValueError("模型尚未训练，无法进行预测")
        
        if output_file is None:
            output_file = self.output_dir / "predictions.csv"
        
        print(f"使用内存映射进行预测，数据文件: {data_file}")
        
        # 使用内存映射读取大文件
        with open(data_file, 'r') as f:
            # 创建内存映射
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            
            # 分批读取和预测
            batch_size = 1000000  # 每批处理的行数
            results = []
            
            mm.seek(0)
            line = mm.readline().decode('utf-8').strip()
            count = 0
            batch_data = []
            
            while line:
                batch_data.append(line)
                count += 1
                
                if count % batch_size == 0:
                    # 处理当前批次
                    dtest = xgb.DMatrix('\n'.join(batch_data))
                    batch_preds = self.model.predict(dtest)
                    results.extend(batch_preds)
                    batch_data = []
                    print(f"已处理 {count} 行")
                
                line = mm.readline().decode('utf-8').strip()
                if not line:
                    break
            
            # 处理最后一批
            if batch_data:
                dtest = xgb.DMatrix('\n'.join(batch_data))
                batch_preds = self.model.predict(dtest)
                results.extend(batch_preds)
            
            mm.close()
        
        # 保存预测结果
        pd.DataFrame({"prediction": results}).to_csv(output_file, index=False)
        print(f"预测结果已保存至: {output_file}")
        
        return output_file


def main():
    """
    主函数，演示如何使用LargeDataXGBoostTrainer处理大规模数据
    """
    # 示例配置
    model_config = {
        "exp_path": "/path/to/data",
        "train_start_time": "20210701",
        "train_end_time": "20230930",
        "valid_start_time": "20231001",
        "valid_end_time": "20231215",
        "symbol_list": ["symbol1", "symbol2", "symbol3"],
        "factor_name_list": ["factor1", "factor2", "factor3"],
        "tagger_name_list": ["target"],
        "xgb_config": {
            "objective": "reg:squarederror",
            "learning_rate": 0.03,
            "max_depth": 8,
            "n_estimators": 1000,
            "subsample": 0.7,
            "colsample_bytree": 0.7
        }
    }
    
    # 创建训练器实例
    trainer = LargeDataXGBoostTrainer(
        model_config=model_config,
        output_dir="/path/to/output"
    )
    
    # 方法1: 使用外部内存模式训练
    train_file = trainer.prepare_libsvm_file(model_config["symbol_list"], model_config)
    trainer.train_with_external_memory(train_file)
    
    # 方法2: 使用批处理方式训练
    # trainer.train_with_batches(model_config["symbol_list"], batch_size=5)
    
    # 保存模型
    trainer.save_model()
    
    print("大规模数据训练完成！")


if __name__ == "__main__":
    main()