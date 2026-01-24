import re
import logging
import time
from datetime import datetime
import httpx
import json
from typing import Dict
logger = logging.getLogger(__name__)

import requests
from lxml import etree


def get_element_text(url):
    """获取XPath对应元素的文本和属性"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding

        # 解析HTML
        html = etree.HTML(response.text)

        # XPath定位
        xpath_locator = '//*[@id="__pm_layout"]/div[2]/div/div[2]/div/div/div/div/div/div/div[1]/div/div/div[1]/div[2]/a'
        elements = html.xpath(xpath_locator)

        if elements:
            element = elements[0]

            # 获取各种字段
            result = {
                'text': element.text or '',
                'href': element.get('href', ''),
                'class': element.get('class', ''),
                'id': element.get('id', ''),
                'title': element.get('title', ''),
                'all_attributes': dict(element.attrib)
            }
            return result
        else:
            print("❌ 未找到元素")
            return None

    except Exception as e:
        print(f"❌ 错误: {e}")
        return None


def fetch_market_from_slug(slug: str) -> Dict[str, any]:
    url = f"https://gamma-api.polymarket.com/events/slug/{slug}"
    res = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()
    ret = json.loads(res.text)
    return ret

def get_top_holders(id: str):
    url = f"https://data-api.polymarket.com/holders"
    params = {
        "limit": 5,
        "market": id,
        "minBalance": 1
    }

    response = httpx.get(
        url,
        params=params,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()
    ret = json.loads(response.text)
    return ret


def display_with_full_url(data):
    """美化显示，增加Polymarket URL列宽"""

    outcome_0 = [
        {
            'pseudonym': h['pseudonym'],
            'amount': h['amount'],
            'proxyWallet': h['proxyWallet'],
            'name_url': f"https://polymarket.com/@{h['name']}",
            'name': f"https://polygonscan.com/address/{h['proxyWallet']}"
        }
        for market in data
        for h in market['holders']
        if h['outcomeIndex'] == 0
    ]

    outcome_1 = [
        {
            'pseudonym': h['pseudonym'],
            'amount': h['amount'],
            'proxyWallet': h['proxyWallet'],
            'name_url': f"https://polymarket.com/@{h['name']}",
            'name': f"https://polygonscan.com/address/{h['proxyWallet']}"
        }
        for market in data
        for h in market['holders']
        if h['outcomeIndex'] == 1
    ]

    # 显示 Outcome 0
    print("=" * 220)
    print("📊 OUTCOME 0 (YES)")
    print("=" * 220)
    print(f"{'#':<4} {'Pseudonym':<22} {'Amount':>12} {'Wallet':<44} {'Polymarket URL':<85} {'Polygonscan URL':<75}")
    print("-" * 220)

    for i, item in enumerate(outcome_0, 1):
        print(
            f"{i:<4} "
            f"{item['pseudonym']:<22} "
            f"{item['amount']:>12,.2f} "
            f"{item['proxyWallet']:<44} "
            f"{item['name_url']:<85} "  # 增加到85字符
            f"{item['name']:<75}"
        )

    total_0 = sum(item['amount'] for item in outcome_0)
    print("-" * 220)
    print(f"{'Total:':<38} {total_0:>12,.2f}")
    print(f"{'Count:':<38} {len(outcome_0):>12}")

    # 显示 Outcome 1
    print("\n" + "=" * 220)
    print("📊 OUTCOME 1 (NO)")
    print("=" * 220)
    print(f"{'#':<4} {'Pseudonym':<22} {'Amount':>12} {'Wallet':<44} {'Polymarket URL':<85} {'Polygonscan URL':<75}")
    print("-" * 220)

    for i, item in enumerate(outcome_1, 1):
        print(
            f"{i:<4} "
            f"{item['pseudonym']:<22} "
            f"{item['amount']:>12,.2f} "
            f"{item['proxyWallet']:<44} "
            f"{item['name_url']:<85} "  # 增加到85字符
            f"{item['name']:<75}"
        )

    total_1 = sum(item['amount'] for item in outcome_1)
    print("-" * 220)
    print(f"{'Total:':<38} {total_1:>12,.2f}")
    print(f"{'Count:':<38} {len(outcome_1):>12}")

    return outcome_0, outcome_1


if __name__ == '__main__':
    while True:
        res = get_element_text("https://polymarket.com/crypto/15M")
        slug = res['href'].split('/')[-1]
        print(slug)
        res_market  = fetch_market_from_slug(slug)['markets'][0]
        market_id = res_market['conditionId']
        res_top_holders = get_top_holders(market_id)
        display_with_full_url(res_top_holders)
        time.sleep(10)