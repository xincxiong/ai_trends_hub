# -*- coding: utf-8 -*-
"""域名白名单与渠道关键词，用于召回过滤与来源归一化。"""

REUTERS_SYNDICATION = {
    "finance.yahoo.com", "uk.finance.yahoo.com", "www.msn.com", "msn.com",
    "investing.com", "marketscreener.com", "nasdaq.com", "marketwatch.com",
}

CHINA_OFFICIAL_DOMAINS = {
    "tencent.com", "cloud.tencent.com", "aliyun.com", "baidu.com",
    "huawei.com", "huaweicloud.com", "jdcloud.com", "volcengine.com",
    "ctyun.cn", "ecloud.10086.cn", "unicom.cn",
}

CHINA_GPU_COMPANY_DOMAINS = {
    "hiascend.com", "hygon.cn", "brchip.com", "mthreads.com",
    "muxi-tech.com", "tianshu.ai",
}
CHINA_OFFICIAL_DOMAINS = CHINA_OFFICIAL_DOMAINS | CHINA_GPU_COMPANY_DOMAINS

CHANNEL_VENDOR_DOMAINS = {
    "gigabyte.com", "gigabyte.com.tw", "gigabytecn.com",
    "asus.com", "msi.com", "supermicro.com", "pny.com",
}

CORE_DOMAINS = {
    "reuters.com", "bloomberg.com", "wsj.com", "ft.com", "economist.com",
    "nikkei.com", "asia.nikkei.com", "digitimes.com", "digitimes-asia.com",
    "venturebeat.com", "techcrunch.com", "theinformation.com",
    "semianalysis.com", "anandtech.com", "tomshardware.com",
    "arstechnica.com", "nextplatform.com", "servethehome.com", "theregister.com",
    "caixin.com", "yicaiglobal.com",
    "tencent.com", "cloud.tencent.com", "aliyun.com", "huawei.com", "huaweicloud.com",
} | REUTERS_SYNDICATION

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

CHINA_MEDIA_DOMAINS = {
    "xinhuanet.com", "people.com.cn", "cctv.com", "chinanews.com.cn",
    "stcn.com", "eastmoney.com", "10jqka.com.cn",
    "36kr.com", "huxiu.com", "tmtpost.com", "jiemian.com",
    "laoyaoba.com", "semiinsights.com", "qq.com", "sina.com.cn",
}
SECONDARY_DOMAINS = SECONDARY_DOMAINS | CHINA_MEDIA_DOMAINS

LLM_PRIMARY_SOURCES = {
    "openai.com", "anthropic.com", "blog.google", "deepmind.google", "meta.com",
    "huggingface.co", "github.com", "arxiv.org",
    "modelscope.cn", "qwenlm.ai", "zhipuai.cn", "moonshot.cn", "minimax.chat",
}
SECONDARY_DOMAINS = SECONDARY_DOMAINS | LLM_PRIMARY_SOURCES

CHANNEL_VENDOR_KEYWORDS = [
    "GIGABYTE", "Gigabyte", "技嘉", "Supermicro", "超微",
    "ASUS", "华硕", "MSI", "微星", "PNY",
    "TD SYNNEX", "Ingram Micro", "Arrow", "Avnet",
]
