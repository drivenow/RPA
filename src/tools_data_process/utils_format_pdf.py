test_lazy_html = """<html><body><p>'









</p><div>
<div>
<div>
<div>
<img alt="cover_image" class="wx_follow_avatar_pic" src="https://mmbiz.qpic.cn/sz_mmbiz_jpg/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoB2hykr6Wf12yaIWmN4xZrMIpzYDRib97TJsV3JngbALouQbn92ibdiad0A/0?wx_fmt=jpeg"/>
</div>
<div>
<div>
<div>
<h1>
买卖压力度量，复权调整成交量之后，效果居然能有提升！</h1>
<div>
<span>原创&lt;
/span&gt;
<span>
                   量化拯救散户
                 </span>
<span>
<a href="javascript:void(0);">
        量化拯救散户
</a>
</span>
<span>
<em>2025年10月25日
14:25</em>
<em><span>上海</span></em>
</span>
</span></div>
<div><section><section><s ection=""><section><section><img _width="100%" class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" data-="" data-imgfileid="100007369" data-index="1" data-original-style="vertical-align: middle;max-width: 100%;width: 100%;box-
sizing: border-box;height: auto !important;" data-ratio="0.8034188034188035" data-s="300,640" data-type="gif" data-w="351" height="1" src="https://mmbiz.qpic.cn/sz_mmbiz_gif/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBBBDFMLxAeg23Lh8Gs2kd42CxrUutIL75E5oZk8icfvs122OJ8g4wickQ/640?wx_fmt=png&amp;from=appmsg" style="vertical-align:
middle; max-width: 100%; box-sizing: border-box; width: 110px !important;
height: 88.3761px !important; visibility: visible;" width="1"/></section></section></s></section></section><section><p><span><img _width="677px" class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" data-="" data-imgfileid="100007391" data-index="2" data-original-style="height: auto
!important;" data-ratio="0.562962962962963" data-type="jpeg" data-w="1080" height="1" src="https://mmbiz.qpic.cn/sz_mmbiz_jpg/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBdVk3zYp1xXibYTM01vuI5MicMurLDXFY93l7kSSxEwuZz1vYboiaK6HgQ/640?wx_fmt=jpeg&amp;from=appmsg" style="width: 637px
!important; height: 358.607px !important; visibility: visible;" width="1"/></span><span>本文，笔者将复现东方证券朱剑涛老师2019年10月29日发布的研报《</span><span>因子选股系列研究之
六十：基于量价关系度量股票的买卖压力</span><span>》。</span></p><p><span>2019年的时候，因子选股系列已经发布了60篇了，这含
金量无需多言。</span></p><p><span>研报中，认为市场上存在两类投资者，A类着眼于中长期，B类看中短期。所以，B类投资者的交易是噪声交易。</span></p><p><span>通过对A类投资者的分析，这类投资者买入的时候，标的在价格低位的成交量大于价格高位；卖出的时候，标的在价格高位的成交量大于价格低
位。</span></p><p><span>基于这样的一个思路，就有了这个叫做<span>买卖压力度量</span>的因子。</span></p><section><section><section><section><section><section><p><strong><span>计算步骤及代
码</span></strong></p></section></section></section></section></section></section><section><section><section><p><span>这个因子的计算步骤不是很复杂，用一个公式就能表达。</span></p><section><section><section><section><section><p><strong><span>1</span></strong></p></section></section><section><section><p><strong><span>计算公式</span></strong></p></section></section></section></section></section><section><section><sectio n=""><section><section><section><img _width="677px" class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" data-="" data-imgfileid="100007379" data-index="3" data-original-style="height: auto !important;" data-ratio="0.24615384615384617" data-s="300,640" data-type="png" data-w="780" height="1" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoB8YvwH9pOpLiaIvo7Mvakok6Qv3cwQLBe7twR2lr4bCfswk9r5RV79ag/640?wx_fmt=png&amp;from=appmsg" style="width: 524px
!important; height: 128.985px !important;" type="block" width="1"/></section><p><span>vwap很好理解，就是成交量加权平均价格。</span></p><p><span>volu就是vol
ume，成交量。</span></p><p><span>此外，在研报中还隐藏了一个细节，那就是vwap和volu都是经过复权调整的。</span></p><p>
<span>说实话，笔者不是很理解这一句话，主要是成交量是如何经过复权调整的。</span></p><p><span>实在想不明白，笔者就简单粗暴，直接将成交量
乘上了复权因子。</span></p></section></section></sectio></section></section></section><section><s ection=""><section><section><section><p><b><span>2</span></b></p></section><section><section><p><strong><span>计算代码</span></strong></p></section></section></section></section></s></section><section><section><section><section><section><sec tion=""><pre><code><span>def __call__(self):</span></code><code><span>   
data =
BaseDataLoader.<span>load_data</span>(<span>'../../data/stock_bar_1day.parquet'</span>,</span></code><code><span>                 
                     
 fields=[<span>'vwap'</span>, <span>'volume'</span>, <span>'factor
'</span>]).<span>to_dataframes</span>()</span></code><code><span>   
self.vwap = data[<span>'vwap'</span>] *
data[<span>'factor'</span>]</span></code><code><span>    self.vol =
data[<span>'volume'</span>] *
data[<span>'factor'</span>]</span></code><code><span>    res =
[]</span></code><code><span>    for i
in <span>tqdm</span>(<span>range</span>(<span>21</span>, <span>len</span>(
self.vwap)+<span>1</span>)):</span></code><code><span>       
res.<span>append</span>(self.<span>cal_factor</span>(i))</span></code><code><spa n="">    res = pd.<span>concat</span>(res,
axis=<span>1</span>).T</spa></code><code><span>    res.index.name
= <span>'datetime'</span></span></code><code><span>   
res.<span>reset_index</span>(inplace=True)</span></code><code><span>   
res = pd.<span>melt</span>(res, id_vars=<span>'datetime'</span>,
var_name=<span>'code'</span>,
value_name=<span>'reverse_prob'</span>)</span></code><code><span>   
res.<span>to_parquet</span>(<span>'./reverse_prob.parquet'</span>)</span></code></pre></sec></section><p><span>第一段代码，主要就是读取数据。主要是第4行和第5行，需要说明一下，这两行的作用就是对vwap和volu进行
复权调整。</span></p><section><pre><code><span><span>def</span> <span>cal_factor
span&gt;(<span><span>self</span></span><span>,
idx</span>):</span></span></code><code><span>    vwap
= <span>self</span>.vwap.iloc[idx-
<span>21</span><span>:idx</span>]</span></code><code><span>    day =
vwap.iloc[[-
<span>1</span>]].index.tolist()[<span>0</span>]</span></code><code><span> 
  vol = <span>self</span>.vol.iloc[idx-
<span>21</span><span>:idx</span>]</span></code><code><span>    vol =
vol.div(vol.mean(), axis=<span>1</span>)</span></code><code><span>    res
= np.log(vwap.mean() / (vwap * vol).sum())</span></code><code><span>   
res.name = day</span></code><code><span> 
  <span>return</span> res</span></code></pre></section><p><span>第二段代码，就
是按照公式计算每21个交易日的因子值。</span></p></section></section></section></section></section>
<section><section><section><img _width="100%" class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" data-="" data-imgfileid="100007371" data-index="4" data-original-style="vertical-align: middle;max-width: 100%;width: 100%;box-
sizing: border-box;height: auto !important;" data-ratio="0.9203703703703704" data-s="300,640" data-type="png" data-w="1080" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBzxKibSosaw9MmOH3F8aOfySIs1llHN9KgTlq1ERVPHaDqW9xjHWz31g/640?wx_fmt=png&amp;from=appmsg" style="vertical-align:
middle; max-width: 100%; box-sizing: border-box; width: 53px !important; height:
48.7796px
!important;"/></section></section></section></section></section><section><sectio n=""><section><section><section><section><p><strong><span>因子评价</span></strong></p>&lt;
/section&gt;</section></section></section></section></sectio></section><section><section><se ction=""><p><span>由于这个因子在计算的时候已经使用了过去21个交易日的量价数据了，所以它本身就可以看作是一个月度因子了，无需在对过去21个交易日的因
子值取均值或者标准差了。</span></p><p><span>值得一提的是，笔者在复现的时候也尝试过，对vwap进行复权，而不对volu进行复权，得到的因子表
现不如都复权处理的。所以，下面的因子评价结果展示的是对vwap和volu都复权处理计算的因子。</span></p></se></section><section><se ction=""><section><section><section><section><section><section><section><section><p><strong><span>01</span></strong></p></section></section></section></section></section></section><section><section><p><strong><span>IC分析</span></strong></p></section></section></section></section></se></section><section><section><secti on=""><section><section><section><section><section><img _width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder wx_img_placeholder" data-="" data-imgfileid="100007380" data-index="5" data-original-="" data-ratio="0.75" data-s="300,640" data-type="png" data-w="1080" height="1" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBPQKqN9x2PYjeDN3Jicj9oOnayGHOgPnByg0gfCP2nHxUjz8r9cqpPKg/640?wx_fmt=png&amp;from=appmsg" style="height: auto !important;" type="block" width="1"/></section><section><img _width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder wx_img_placeholder" data-="" data-index="6" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-type="png" data-w="1080" height="1" imgfileid="100007383" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoB63qwR6wPXIUbTSpAKGibjfl8uJpLVT2YTTrkwYtWW7Ltl3AwkqKKtxA/640?wx_fmt=png&amp;from=appmsg" style="width: 531px
!important; height: 398.25px !important;" type="block" width="1"/></section><section><img _width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder wx_img_placeholder" data-="" data-index="7" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-type="png" data-w="1080" height="1" imgfileid="100007384" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBHqo7MMCDicByhxIf66loRCh3WyPDuepK3RkJeJChoTiaveRUCElWaic3A/640?wx_fmt=png&amp;from=appmsg" style="width: 531px
!important; height: 398.25px !important;" type="block" width="1"/></section><section><img _width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder wx_img_placeholder" data-="" data-index="8" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-type="png" data-w="1080" height="1" imgfileid="100007382" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBibOYXMJdvHselZmTLibRjENwpZicKKvA69PdPpdGNTmmD9FCRrCuQIJqQ/640?wx_fmt=png&amp;from=appmsg" style="width: 531px
!important; height: 398.25px !important;" type="block" width="1"/></section><section><img _width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder wx_img_placeholder" data-="" data-index="9" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-type="png" data-w="1080" height="1" imgfileid="100007381" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBdDnfoGyZo5sWq8r4HbPx68PveewIT75TwrtLPsbj1fdE64n2drBzEg/640?wx_fmt=png&amp;from=appmsg" style="width: 531px
!important; height: 398.25px !important;" type="block" width="1"/></section><section><img _width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder wx_img_placeholder" data-="" data-index="10" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-type="png" data-w="1080" height="1" imgfileid="100007385" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBdJ1NCzTrxyaX5nocLaMRialye305FrI0NKZmKib1wwpXBqVZeA5QIxKQ/640?wx_fmt=png&amp;from=appmsg" style="width: 531px
!important; height: 398.25px !important;" type="block" width="1"/></section><p><span>从IC上来看，这个因子的表现中规中矩，IC绝对值不算高也不能说低。</span></p></section></section></section></section></secti></section></section><section><sectio n=""><section><section><section><section><section><section><section><section><p><st rong=""><span>02</span></st></p></section></section></section></section></section></section><section><section><p><strong><span>回归分析</span></strong>
p&gt;</p></section></section></section></section></sectio></section><section><section><section>&lt;
section&gt;<section><section><section><section><img _width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder wx_img_placeholder" data-="" data-imgfileid="100007386" data-index="11" data-original-="" data-ratio="0.75" data-s="300,640" data-type="png" data-w="1080" height="1" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBbjd2SaJ9iaerl4x6ntFHcj7gXxicqGeQBD25RiaXUD7qaljVEFu2AOCug/640?wx_fmt=png&amp;from=appmsg" style="height: auto !important;" type="block" width="1"/></section><section><img _width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder wx_img_placeholder" data-="" data-index="12" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-type="png" data-w="1080" height="1" imgfileid="100007387" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBK5icbYEc2vZdqpkDIL2GSBGzBcsfHQ37y6omiaAOgIpCGyIAxCYx2LiaQ/640?wx_fmt=png&amp;from=appmsg" style="width: 531px
!important; height: 398.25px !important;" type="block" width="1"/></section></section></section></section></section></section></section></section><section><section><section><section><section><section><section><secti on=""><section><section><p><strong><span>03</span></strong></p></section></section>
</secti></section></section></section></section></section><section><section><p><strong>&lt;
span&gt;换手率分析</strong></p></section></section></section></section>
<section><section><section><section><section><section><section><section><img _width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder wx_img_placeholder" data-="" data-imgfileid="100007389" data-index="13" data-original-="" data-ratio="0.75" data-s="300,640" data-type="png" data-w="1080" height="1" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBhfPLicjTzq7E4B65cZlxTADE5NuTNN5Am9o08odt06dSkZB2VUsvLbw/640?wx_fmt=png&amp;from=appmsg" style="height: auto !important;" type="block" width="1"/></section><section><img _width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder wx_img_placeholder" data-="" data-index="14" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-type="png" data-w="1080" height="1" imgfileid="100007390" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBib3CU6qldWxS1zBw6RBmeQX1TiaJSEyqKiajAKe66cPR97PPa7zqfuu7Q/640?wx_fmt=png&amp;from=appmsg" style="width: 531px
!important; height: 398.25px !important;" type="block" width="1"/></section></section></section></section></section></section></section></section><section><section><section><section><section><section><section><secti on=""><section><section><p><strong><span>04</span></strong></p></section></section>
</secti></section></section></section></section></section><section><section><p><strong>&lt;
span&gt;鼓励创新原则</strong></p></section></section></section></section><section><section><section><section><section><section><section><section><img _width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder wx_img_placeholder" data-="" data-imgfileid="100007388" data-index="15" data-original-="" data-ratio="0.75" data-s="300,640" data-type="png" data-w="1080" height="1" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBKyezUlialibBzOktNEJCktc3H48taumX0OibjVZOm0lOsjjzia0vrcMJCQ/640?wx_fmt=png&amp;from=appmsg" style="height: auto !important;" type="block" width="1"/></section><p><span>但是，分层回测上的表现注定了这个因子恐怕很难被使用。</span></p><p><span>因为，其
分层回测的单调性可以说是一塌糊涂，因子值最小的一组和因子值最大的一组的收益率小于其他三组。</span></p><p><span>如果在考虑交易成本的话，无论是
因子值最大的一组还是因子值最小的一组，其在2018年到2024年间的收益率都将是小于0的。</span></p></section></section></section></section></section></section><section><section><section><img _width="100%" class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" data-="" data-imgfileid="100007372" data-index="16" data-original-style="vertical-align:
middle;max-width: 100%;width: 100%;box-sizing: border-box;height: auto
!important;" data-ratio="0.9203703703703704" data-s="300,640" data-type="png" data-w="1080" src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBzxKibSosaw9MmOH3F8aOfySIs1llHN9KgTlq1ERVPHaDqW9xjHWz31g/640?wx_fmt=png&amp;from=appmsg" style="vertical-align:
middle; max-width: 100%; box-sizing: border-box; width: 53px !important; height:
48.7796px
!important;"/></section></section></section></section><section><p><str ong=""><span><span>- </span><span><em><span>END</span></em></span><span> -
</span></span></str></p></section><section><section><section><img _width="100%" class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" data-imgfileid="100007376" data-index="17" data-original-style="vertical-align: middle;max-width: 100%;width: 100%;box-sizing: border-box;height: auto !important;" data-ratio="0.8034188034188035" data-s="300,640" data-src="https://mmbiz.qpic.cn/sz_mmbiz_gif/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBBBDFMLxAeg23Lh8Gs2kd42CxrUutIL75E5oZk8icfvs122OJ8g4wickQ/640?wx_fmt=png&amp;from=appmsg" data-type="gif" data-w="351" height="1" src="https://mmbiz.qpic.cn/sz_mmbiz_gif/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBBBDFMLxAeg23Lh8Gs2kd42CxrUutIL75E5oZk8icfvs122OJ8g4wickQ/640?wx_fmt=png&amp;from=appmsg" style="vertical-align: middle; max-width: 100%; box-sizing: border-box; width: 110px !important; height: 88.3761px !important;" width="1"/></section></section></section></div>
</div>
<div>预览时标签不可点</div>
</div>
</div>
<div>
<div>
<div>
<p>微信扫一扫关注该公众号</p>
</div>
</div>
</div>
</div>
<div>
<div>
<span>继续滑动看下一个</span>
</div>
</div>
</div>
<div>
<div>
<div>
<button>轻触阅读原文</button>
</div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<span>
<img alt="" class="wx_follow_avatar_pic" src="http://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGsObOvNt30RgVh2Tsxrx3jqaba7mP6jPoo0ASk2qXCCE8Zb7pqaDM1kO2utfN19R9jrquiavyETaAw/0?wx_fmt=png"/>
</span>
</div>
<div>
<div>
<div>
            量化拯救散户           </div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
<div>
<div>
<div>
<span>向上滑动看下一个</span>
</div>
</div>
</div>
</div>
<div>
<div>
<div>
<a href="javascript:;">知道了</a>
</div>
</div>
</div>
<div>
<div>
<div>
     微信扫一扫使用小程序
</div>
</div>
</div>
<div>
<div>
<div>
<a href="javascript:void(0);">取消</a>
<a href="javascript:void(0);">允许</a>
</div>
</div>
</div>
<div>
<div>
<div>
<a href="javascript:void(0);">取消</a>
<a href="javascript:void(0);">允许</a>
</div>
</div>
</div>
<div>
<div>
<div>
<a href="javascript:void(0);">取消</a>
<a href="javascript:void(0);">允许</a>
</div>
</div>
</div>
<div>
<button>×</button>
<button>分析</button>
</div>
<div>
<div>
<div>
<div>
<div>
<img alt="作者头像" class="jump_author_avatar" src="http://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGsObOvNt30RgVh2Tsxrx3jqaba7mP6jPoo0ASk2qXCCE8Zb7pqaDM1kO2utfN19R9jrquiavyETaAw/0?wx_fmt=png"/>
</div>
</div>
</div>
<div>
<p>微信扫一扫可打开此内容，使用完整服务</p>
</div>
</div>
</div>
<span>：</span>
<span>，</span>
<span>，</span>
<span>，</span>
<span>，</span>
<span>，</span>
<span>，</span>
<span>，</span>
<span>，</span>
<span>，</span>
<span>，</span>
<span>，</span>
<span>，</span>
<span>。</span>
<span>视频</span>
<span>小程序</span>
<span>赞</span>
<span>，轻点两下取消赞</span>
<span>在看</span>
<span>，轻点两下取消在看</span>
<span>分享</span>
<span>留言</span>
<span>收藏</span>
<span>听过</span>







'
</div></body></html>"""

# pip install pdfkit
import pdfkit
import os
import platform

def html_to_pdf(html, save_file):
    try:
        # 1) 可选：显式指定 wkhtmltopdf 可执行文件路径
        #    - Windows 常见路径：C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe
        #    - macOS 用 brew 安装后：/usr/local/bin/wkhtmltopdf 或 /opt/homebrew/bin/wkhtmltopdf
        wk_path = r"E:\Program Files\wkhtmltox-0.12.6-1.mxe-cross-win64\wkhtmltox\bin\wkhtmltopdf.exe" if platform.system() == "Windows" else "/usr/local/bin/wkhtmltopdf"
        cfg = pdfkit.configuration(wkhtmltopdf=wk_path) if os.path.exists(wk_path) else None

        # 2) 常用选项（按需增删）
        options = {
            # 解决本地图片/CSS引用被拦：允许访问 file://
            "enable-local-file-access": None,
            # 页面设置
            "page-size": "A4",
            "margin-top": "15mm",
            "margin-right": "12mm",
            "margin-bottom": "15mm",
            "margin-left": "12mm",
            "encoding": "utf-8",
            # 如果页面里有 JS 动态渲染/懒加载，适当等一等（毫秒）
            "javascript-delay": "800",
            # 页眉/页脚示例（用占位符 [page] / [toPage]）
            "header-center": "我的报告",
            "footer-right": "[page]/[toPage]",
            # 遇到资源加载失败不终止（可选）
            "load-error-handling": "ignore",
        }


        # 3) 从 HTML 文件生成 PDF
        # with open("test.html", "w", encoding="utf-8") as f:
        #     f.writelines(test_lazy_html)
        # pdfkit.from_file("test.html", save_file, options=options, configuration=cfg)

        # 也可以：从 HTML 字符串生成
        # html = "<h1>hello</h1>"
        pdfkit.from_string(html, save_file, options=options, configuration=cfg)

        return True

        # 或者：批量多个 HTML 拼成一本 PDF（目录/封面也支持）
        # pdfkit.from_file(["cover.html", "chapter1.html", "chapter2.html"], "book.pdf", options=options, configuration=cfg)
    except Exception as e:
        print("转换pdf文件失败！", e)
        return False
    
if __name__=="__main__":
    html_to_pdf(test_lazy_html, save_file = "output.pdf")