# -*- coding: utf-8 -*-
"""
域名白名单与渠道关键词：数据收集时只从这些域名下的网页抓取/核验。
- 召回阶段（Stage A）与核验阶段（Stage B）均用 domain_allowed() 过滤 URL。
- 来源归一化（如 Reuters 转载）使用 REUTERS_SYNDICATION。
"""

# Reuters 转载站点（source 统一归为 Reuters）
REUTERS_SYNDICATION = {
    "finance.yahoo.com", "uk.finance.yahoo.com", "www.msn.com", "msn.com",
    "investing.com", "marketscreener.com", "nasdaq.com", "marketwatch.com",
}

# 中国官方/云与运营商
CHINA_OFFICIAL_DOMAINS = {
    "tencent.com", "cloud.tencent.com", "aliyun.com", "baidu.com",
    "huawei.com", "huaweicloud.com", "jdcloud.com", "volcengine.com",
    "ctyun.cn", "ecloud.10086.cn", "unicom.cn",
}

# 中国 GPU/芯片公司
CHINA_GPU_COMPANY_DOMAINS = {
    "hiascend.com", "hygon.cn", "brchip.com", "mthreads.com",
    "muxi-tech.com", "tianshu.ai",
}
CHINA_OFFICIAL_DOMAINS = CHINA_OFFICIAL_DOMAINS | CHINA_GPU_COMPANY_DOMAINS

# 重点“技嘉这一类”：AIB/系统商/板卡/服务器
CHANNEL_VENDOR_DOMAINS = {
    "gigabyte.com", "gigabyte.com.tw", "gigabytecn.com",
    "asus.com", "msi.com", "supermicro.com",
    "pny.com",
}

# 核心信源（权威媒体 + 科技/半导体 + 中国云）
CORE_DOMAINS = {
    "reuters.com", "bloomberg.com", "wsj.com", "ft.com", "economist.com",
    "nikkei.com", "asia.nikkei.com", "digitimes.com", "digitimes-asia.com",
    "venturebeat.com", "techcrunch.com", "theinformation.com",
    "semianalysis.com", "anandtech.com", "tomshardware.com",
    "arstechnica.com", "nextplatform.com", "servethehome.com", "theregister.com",
    "caixin.com", "yicaiglobal.com",
    "tencent.com", "cloud.tencent.com", "aliyun.com", "huawei.com", "huaweicloud.com",
} | REUTERS_SYNDICATION

# “不一定权威但真实”：行业研究/报价/渠道信号常见来源（Stage B 核验后入库）
CHANNEL_AND_MEMORY_SOURCES = {
    "trendforce.com", "dramexchange.com",
    "tomshardware.com", "anandtech.com", "servethehome.com", "theregister.com",
    "wccftech.com", "videocardz.com", "guru3d.com",
}

SECONDARY_DOMAINS = {
    "cnbc.com", "axios.com", "theverge.com", "wired.com", "forbes.com",
    "nvidia.com", "amd.com", "intel.com", "tsmc.com", "samsung.com",
    "skhynix.com", "micron.com",
    "whitehouse.gov", "commerce.gov", "bis.doc.gov", "sec.gov",
    "prnewswire.com", "businesswire.com",
} | CHANNEL_AND_MEMORY_SOURCES | CHANNEL_VENDOR_DOMAINS

# 中国财经/科技媒体
CHINA_MEDIA_DOMAINS = {
    "xinhuanet.com", "people.com.cn", "cctv.com", "chinanews.com.cn",
    "stcn.com", "eastmoney.com", "10jqka.com.cn",
    "36kr.com", "huxiu.com", "tmtpost.com", "jiemian.com",
    "laoyaoba.com", "semiinsights.com", "qq.com", "sina.com.cn",
}
SECONDARY_DOMAINS = SECONDARY_DOMAINS | CHINA_MEDIA_DOMAINS

# 大模型/开源与学术 primary 信源
LLM_PRIMARY_SOURCES = {
    "openai.com", "anthropic.com", "blog.google", "deepmind.google", "meta.com",
    "huggingface.co", "github.com", "arxiv.org",
    "modelscope.cn", "qwenlm.ai", "zhipuai.cn", "moonshot.cn", "minimax.chat",
}
SECONDARY_DOMAINS = SECONDARY_DOMAINS | LLM_PRIMARY_SOURCES

# 重点渠道公司名称（用于查询与抽取）
CHANNEL_VENDOR_KEYWORDS = [
    "GIGABYTE", "Gigabyte", "技嘉",
    "Supermicro", "超微",
    "ASUS", "华硕",
    "MSI", "微星",
    "PNY",
    # 也可加你关心的总代/分销商：
    "TD SYNNEX", "Ingram Micro", "Arrow", "Avnet",
]
