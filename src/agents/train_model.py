import os
import gc
import datetime
import sys
import shutil
import pickle
from tqdm import tqdm
import polars as pl
from xgboost import XGBRegressor, XGBClassifier
import numpy as np
import pandas as pd
import copy
import time
import json
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from sklearn.metrics import mean_squared_error as mse
import ray
from artifacts import exp_artifacts, model_save_and_evaluate, parse_format, backtest_save_and_evaluate, model_plot
from artifacts.flying_functions import *
from artifacts.utils import save_backtest_result
from xquant.factordata import FactorData

pd.set_option('display.max_colwidth', 200)
pd.set_option('display.max_rows', 200)

"""
20240408：训练数据去除上市前30天，挑选训练集去除刚上市
"""


class L2PXGBoostRegPack:
    def __init__(self, exp_name, model_config, version_alias):
        self.data_type = "tick_l2p"
        self.expa = exp_artifacts.ExpArtifacts(exp_name=exp_name, exp_base="/dfs/group/800657/exp_results/")
        self.exp_path = self.expa.exp_path
        self.expa.activate_version_to_save(model_config, version_alias=version_alias)
        self.version_alias = version_alias
        self.model_config = model_config
        self.factor_name_list = model_config["factor_name_list"]
        self.tagger_name_list = model_config["tagger_name_list"]
        self.symbol_list = model_config["symbol_list"]
        self.exp_version_path = self.expa.path_of_exp_version()
        self.fp = FactorProvider('016884')



    def train_loop(self, model_params):
        ########################################################
        exp_path = self.exp_path
        exp_version_path = self.exp_version_path
        model_config = self.model_config
        symbol_list = model_config["symbol_list"]
        flying_factor = select_factors[:2]  # model_config["data_config"]["flying_factors"]
        model_config["data_config"]["flying_factors"] = flying_factor
        flying_factor = []

        T_train_list, X_train_list, Y_train_list, T_valid_list = [], [], [], []
        X_valid_list, Y_valid_list, T_test_list, X_test_list, Y_test_list = [], [], [], [], []

        for symbol in tqdm(symbol_list):
            try:
                if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_label.parquet".format(symbol))):
                    print("无该标的因子数据：", symbol)
                    continue
                print("train_loop: ", symbol)
                open_flying_factor_df = pl.read_parquet(
                    os.path.join(exp_path, "dataset/{}_flying_factor.parquet".format(symbol))).filter(
                    (pl.col("DateTime") >= pl.lit(model_config["train_start_time"]).str.to_datetime("%Y%m%d")) &
                    (pl.col("DateTime") <= pl.lit(model_config["valid_end_time"]).str.to_datetime("%Y%m%d"))).filter(
                    ~pl.col("DateTime").dt.strftime("%Y%m%d").is_in(model_config["filter_time"])
                )

                open_flying_label_df = pl.read_parquet(
                    os.path.join(exp_path, "dataset/{}_flying_label.parquet".format(symbol))).filter(
                    (pl.col("DateTime") >= pl.lit(model_config["train_start_time"]).str.to_datetime("%Y%m%d")) &
                    (pl.col("DateTime") <= pl.lit(model_config["valid_end_time"]).str.to_datetime("%Y%m%d"))).filter(
                    ~pl.col("DateTime").dt.strftime("%Y%m%d").is_in(model_config["filter_time"])
                )
                open_flying_df = open_flying_factor_df.join(open_flying_label_df, on="DateTime")
                print(f"open_flying_factor_df shape: {open_flying_factor_df.shape}, open_flying_label_df shape: {open_flying_label_df.shape}")
                ########################划分训练测试集################################
                T_train, X_train, F_train, Y_train = generate_split_dataset(model_config, open_flying_df,
                                                                            model_config["data_config"]["tagger_limit"],
                                                                            type="train", include_flying_factor=False)
                T_valid, X_valid, F_valid, Y_valid = generate_split_dataset(model_config, open_flying_df,
                                                                            model_config["data_config"]["tagger_limit"],
                                                                            type="valid", include_flying_factor=False)
                # 将收益率转换为对数收益
                if model_config["data_config"]["tagger_log"]:
                    Y_train = np.emath.logn(2, np.abs(Y_train) + 1.2) * np.sign(
                        Y_train)  # 将收益率转换到偏移对数区间，使得乘数收益值为1以下有效，且乘数收益[1.0, 1.1, 1.2]映射为对数收益[1.13,1.20,1.26]
                    Y_valid = np.emath.logn(2, np.abs(Y_valid) + 1.2) * np.sign(Y_valid)

                X_train = X_train.astype(np.float32)
                X_valid = X_valid.astype(np.float32)

                print("mask shape:", symbol, T_train.shape, Y_train.flatten())
                T_train = T_train[-1000000:]
                X_train = X_train[-1000000:]
                Y_train = Y_train[-1000000:]

                T_train_list.append(T_train[-1000000:])
                X_train_list.append(X_train[-1000000:])
                Y_train_list.append(Y_train[-1000000:])
                T_valid_list.append(T_valid)
                X_valid_list.append(X_valid)
                Y_valid_list.append(Y_valid)
                del F_train
                del F_valid
            except Exception as e:
                print("train_loop error: ", symbol, e)

        T_train_all = np.concatenate(T_train_list)
        X_train_all = np.concatenate(X_train_list)
        Y_train_all = np.concatenate(Y_train_list)
        T_valid_all = np.concatenate(T_valid_list)
        X_valid_all = np.concatenate(X_valid_list)
        Y_valid_all = np.concatenate(Y_valid_list)
        del T_train_list
        del X_train_list
        del Y_train_list
        del T_valid_list
        del X_valid_list
        del Y_valid_list
        del T_test_list
        del X_test_list
        del Y_test_list
        gc.collect()
        ########################################################


        self.model_config["xgb_config"]["n_estimators"] = 2000
        self.model_config["xgb_config"]['tree_method'] = 'hist'
        xgb_regressor = XGBRegressor(**self.model_config["xgb_config"], n_jobs=20)
        print("X_train_all: ", X_train_all.shape, "Y_train_all:", Y_train_all.shape, "X_valid_all:", X_valid_all.shape,
              "Y_valid_all:", Y_valid_all.shape)
        xgb_regressor.fit(X_train_all, Y_train_all,
                          eval_set=[(X_train_all, Y_train_all), (X_valid_all, Y_valid_all)],
                          # xgb_model = xgb_regressor_semiconductor,
                          early_stopping_rounds=8,
                          verbose=True)

        ########################## 模型文件存储 #########################
        self.expa.model_file_save(model_obj=xgb_regressor, mode=["pkl"], overwrite=True)
        for symbol in model_config["symbol_list"]:
            if os.path.exists(os.path.join(cached_norm_dataset, "{}_factor_config.json".format(symbol))):
                shutil.copyfile(os.path.join(cached_norm_dataset, "{}_factor_config.json".format(symbol)),
                                os.path.join(self.exp_version_path, "saved_models/{}_factor_config.json".format(symbol)))
        try:
            exp_factor_path = os.path.join(exp_version_path, f"saved_models/factors.csv")
            if not os.path.exists(exp_factor_path):
                os.makedirs(os.path.join(exp_version_path, f"saved_models"), exist_ok=True)
                with open(exp_factor_path, "w") as f:
                    for factor in select_factors:
                        f.writelines(factor + ",\n")
                # shutil.copyfile("/dfs/group/800657/exp_results/exp_l3_kc50_60s/xgboost_base/saved_models/factors.csv", factor_path)
        except Exception as e:
            print("ERRRO:", e)
        ##################################################
        importance_ = xgb_regressor.feature_importances_
        factor_importance = pd.DataFrame({'factor': select_factors, 'importance': importance_})
        factor_importance = factor_importance.sort_values(by='importance', ascending=False)
        print("factor_importance:", factor_importance)
        self.xgb_regressor = xgb_regressor


  

def main(exp_name, model_config, version_alias, train_mode=True):
    # assert model_config!=None, "model_config不可为None！"
    instance = L2PXGBoostRegPack(exp_name=exp_name,
                                 model_config=model_config,
                                 version_alias=version_alias
                                 )
    if train_mode == True:
        # instance.prepare_data(data_params={})
        instance.train_loop(model_params={})
        instance.xgb_regressor = pd.read_pickle(
            os.path.join(instance.exp_version_path, "saved_models/tmp_model.pickle.dat"))
        instance.predict_signal(instance.xgb_regressor)
    else:
        # 只评价信号，不训练
        instance.xgb_regressor = pd.read_pickle(
            os.path.join(instance.exp_version_path, "saved_models/tmp_model.pickle.dat"))
        # instance.predict_signal(instance.xgb_regressor)


if __name__ == "__main__":
    #######################################################################
    model_config_source = {
        # 数据段配置
        "symbol_list": [],
        "train_start_time": "20210701",
        "train_end_time": "20230930",
        "valid_start_time": "20231001",
        "valid_end_time": "20231215",
        "test_start_time": "20231216",
        "test_end_time": "20240229",
        "factor_name_list": [],  # 按条数筛选后写入
        "tagger_name_list": [],

        "data_config": {
            "data_type": "tick_l2p",
            "w_size": 1,
            "n_job": 2,
            "transform": True,
            "clip_type": "3sigma",
            "scaler_type": "z-score",
            "quantile": [0.02, 0.98],
            "tagger_limit": 60,
            "tagger_log": False, # 是否对收益率取对数
            "tagger_trim": 0, # 是否截取低阈值标签，0表示不截取
            "raw_name_list": [],
            "thres": [-0.020, 0.020],
            "other_factor_list": "",
            # 因子列表， 为空的话为全量
            "factor_json_path": "",
            "levelone_sample_ratio":0.5,
            "sample_method": "sum",
        },
        # 模型段配置
        "xgb_config": {
            'objective': 'reg:squarederror',
            'booster': 'gbtree',
            'tree_method': 'hist',
            'gamma': 0.5,
            'learning_rate': 0.03,
            'lambda': 2,
            'subsample': 0.7,
            'colsample_bytree': 0.7,
            'max_depth': 13,
            'n_estimators': 1300,
            'seed': 4,
        },
        "metrics": {"reg_eval_abs_limits": [1.0, 3.0],
                    "reg_eval_th": 0.5},
        "model_save_mode": ["pkl", "onnx"],
    }
    model_config_source["train_start_time"] = "20240301"
    model_config_source["train_end_time"] = "20250131"
    model_config_source["valid_start_time"] = "20250201"
    model_config_source["valid_end_time"] = "20250228"
    model_config_source["test_start_time"] = "20250301"
    model_config_source["test_end_time"] = "20250428"
    fa = FactorData()
    model_config_source["filter_time"] = fa.tradingday("20240701", "20241031") + fa.tradingday("20250326", "20250410")  # 过滤的日期
    cached_norm_dataset = "/dfs/group/800657/exp_results/zz500_dataset"
    flying_base_dir = "/dfs/group/800657/library/l3_event/event_data"

    ##########################################################################
    df = pd.read_parquet("/dfs/group/800657/tmp/stats.parquet")
    symbols = list(sorted(set(df["symbol"].tolist())))
    df = fa.get_factor_value("Basic_factor", symbols, ["20250506"], ["open"]).reset_index()
    df_index_list = []
    for idx in ["HS300", "ZZ500", "ZZ1000"]:
        sub_df = fa.hset("INDEX", "20250506", idx)
        sub_df["index"] = idx
        df_index_list.append(sub_df)
    df_index = pd.concat(df_index_list)
    df_all = pd.merge(df, df_index, left_on="stock", right_on="stock")
    df_all[(df_all["open"] >= 10)]
    # symbol_list = model_config_source["symbol_list"]
    SYMBOL_LIST = df_all[(df_all["open"] >= 15)]["stock"].tolist()[::2][:200]
    print(len(SYMBOL_LIST))

    factor_save_path = "/dfs/group/800657/exp_results/zz500_dataset/factors_cpp.csv"
    select_factors = pd.read_csv(factor_save_path, header=None)[0].tolist()
    select_factors = [i for i in select_factors if i not in ['FactorActivePV',
                                                             'FactorAvgOutRatio_n_tick20',
                                                             'FactorAvgSpreadGap',
                                                             'FactorAvgVWapSpreadGap',
                                                             'FactorBidAskSpread_n_tick10',
                                                             'FactorBookBuySell15QtyRatiomaxsize',
                                                             'FactorBookSell15Move1QtyDeltaDy0TickQtyRatio',
                                                             'FactorGuangFaTechIndicatorSROC_n_tick20',
                                                             'FactorGuangFaTechIndicatorWAD_n_tick20',
                                                             'FactorNSWPriceVPercent',
                                                             'FactorPxVolCorr_n_tick30',
                                                             'FactorVixDown_n_tick40',
                                                             'FactorVixUp_n_tick40']]
    ##########################################################################

    flying_factor = []
    if (len(flying_factor) > 60):
        flying_base_dir = "/dfs/group/800657/library/l3_event/merge_event_data"
    else:
        flying_base_dir = "/dfs/group/800657/library/l3_event/event_data"
    #######################################################################
    model_config_source["data_config"]["flying_factor"] = flying_factor
    model_config_source["symbol_list"] = SYMBOL_LIST
    model_config_source["tagger_name_list"] = []  # "LabelFirstPeak_th10_60s"
    model_config_source["factor_name_list"] = select_factors
    ###################################################
    # /data/user/013150/online_scripts/shen/DolphindbFactors/labels/InfoTech/Factors
    for label_name, exp_name, version_alias in [
        ("LabelFirstPeak_th10_120s", "exp_l3_flying5", 'LabelFirstPeak_th10_120s_factorcpp_noflying_log2')
    ]:

        # 用幅度特征替代0、1特征
        model_config = copy.deepcopy(model_config_source)
        if "amp" in version_alias:
            flying_factor1 = copy.deepcopy(flying_factor)
            flying_factor1[:5] = ["FacPriceSpread", "FacOneBigOrder", "FacOneBigOrderExtend", "FacCumOrdersNetVolOverV0", "FacBreakingP0NumOrders"]
            model_config["data_config"]["flying_factor"] = flying_factor1

        if not "facevent" in version_alias:
            flying_factor1 = copy.deepcopy(flying_factor)
            model_config["data_config"]["flying_factor"] = flying_factor1[:5]

        if "688981" in version_alias:
            SYMBOL_LIST1 = copy.copy(SYMBOL_LIST)
            model_config["symbol_list"] = ["688981.SH"]

        # 区分高收益率标的和低收益率标签分别训练
        if version_alias in ["LabelFirstPeak_th12_60s_factor98_lowpca", "LabelFirstPeak_th05_60s_factor98_lowpca", "LabelFirstPeak_th10_60s_factor98_lowpca", "LabelFirstPeak_th12_60s_factor98_lowpca_log2"]:
            SYMBOL_LIST = ['688122.SH','603379.SH','600536.SH','688005.SH','688012.SH','002738.SZ','300558.SZ','688297.SH','600563.SH','603939.SH','600378.SH','688778.SH','688363.SH','688281.SH','688981.SH','688271.SH','600329.SH','688187.SH','300114.SZ','603444.SH','688008.SH','688235.SH','600566.SH','000423.SZ','688220.SH','002756.SZ','603160.SH','600298.SH','688002.SH','002281.SZ','002028.SZ','002223.SZ','002409.SZ','600038.SH','300037.SZ','603338.SH','300373.SZ','603882.SH','300073.SZ','688396.SH','603589.SH','002432.SZ','688568.SH','688375.SH','688777.SH','688029.SH','688520.SH','000988.SZ']
            model_config["symbol_list"] = SYMBOL_LIST
        if version_alias in ["LabelFirstPeak_th12_60s_factor98_highpca", "LabelFirstPeak_th05_60s_factor98_highpca", "LabelFirstPeak_th10_60s_factor98_highpca", "LabelFirstPeak_th12_60s_factor98_highpca_log2"]:
            SYMBOL_LIST = ['688521.SH','300418.SZ','688017.SH','688361.SH','002865.SZ','300474.SZ','688348.SH','688082.SH','688390.SH','688200.SH','688041.SH','688276.SH','688385.SH','688063.SH','688037.SH','603786.SH','688099.SH','688153.SH','603688.SH','688047.SH','002850.SZ','603596.SH','688048.SH','688114.SH','688301.SH','300724.SZ','688318.SH','600129.SH','688120.SH','688234.SH','002192.SZ','300502.SZ','688072.SH','688180.SH','688032.SH','300394.SZ','688052.SH','688169.SH','688409.SH','002791.SZ','688331.SH','603606.SH','688598.SH','301236.SZ','688256.SH','688536.SH']
            model_config["symbol_list"] = SYMBOL_LIST

        # 将收益率标签转换为对数收益率
        if "log2" in version_alias:
            model_config["data_config"]["tagger_log"] = True
            # model_config["data_config"]["tagger_trim"] = 0.7 #截取0.5以下的标签


        if "huber" in version_alias:
            model_config["xgb_config"]["objective"] = 'reg:pseudohubererror'
            model_config['xgb_config']["huber_slope"] = float(version_alias[version_alias.find("huber")+5:])
            model_config['xgb_config']['eval_metric'] = 'mae'

        if "lowspread" in version_alias:
            symbols = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/{}_low_spread.csv".format(stock_set), header=None)[0].tolist()
            model_config["symbol_list"] = symbols

        if "midspread" in version_alias:
            symbols = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/{}_mid_spread.csv".format(stock_set), header=None)[0].tolist()
            model_config["symbol_list"] = symbols

        if "highspread" in version_alias:
            symbols = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/{}_high_spread.csv".format(stock_set), header=None)[0].tolist()
            model_config["symbol_list"] = symbols

        model_config["tagger_name_list"] = [label_name]  # "LabelFirstPeak_th10_60s"
        if ray.is_initialized():
            ray.shutdown()
        result_file = f"/dfs/group/800657/exp_results/{exp_name}/{exp_name}_{version_alias}_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        os.makedirs( f"/dfs/group/800657/exp_results/{exp_name}/", exist_ok=True)
        sys.stdout = open(result_file, 'w')
        # sys.stderr = open(result_file, 'w')
        t1 = time.time()
        main(exp_name=exp_name, model_config=model_config, version_alias=version_alias, train_mode = True)
        print("本次试验耗时：", time.time() - t1)
        os.system(f"cp {result_file} /data/user/013150/plot_tmp")
        os.system(f"curl ftp://168.8.2.68/013150/ -T {result_file} -u 'ftphzh:ftphzh2602'")
