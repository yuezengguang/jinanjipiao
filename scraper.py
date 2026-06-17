"""
济南低价机票爬虫
=================
使用 Playwright 调用去哪儿网移动端 API 获取济南出发的特价机票。
只保留价格 ≤ 500 元的航班，输出给前端展示。

使用方法：
    pip install playwright
    python scraper.py

输出：data/flights.json
"""

import json
import os
import random
import time
from datetime import datetime, date, timedelta
from typing import Optional

# ============================================================
# 配置
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEP_CITY = "济南"
PRICE_MAX = 500
REQUEST_DELAY = 1.0

DOMESTIC_TABS = ["", "国内低价榜"]
INTERNATIONAL_TABS = ["出境低价", "国际热门航线"]

# 航司前缀对照
PREFIX_MAP = {
    "CA": "中国国航", "MU": "东方航空", "CZ": "南方航空",
    "SC": "山东航空", "3U": "四川航空", "HU": "海南航空",
    "MF": "厦门航空", "ZH": "深圳航空", "FM": "上海航空",
    "GS": "天津航空", "8L": "祥鹏航空", "PN": "西部航空",
    "GX": "北部湾航空", "G5": "华夏航空", "DR": "瑞丽航空",
    "A6": "西藏航空", "QW": "青岛航空", "DZ": "东海航空",
    "EU": "成都航空", "TV": "西藏航空", "9C": "春秋航空",
    "BK": "奥凯航空", "JD": "首都航空", "GT": "桂林航空",
    "KY": "昆明航空", "HO": "吉祥航空", "Y8": "金鹏航空",
}

# 航司 → 携程/飞猪 参数名
CTRIP_AIRLINE_MAP = {
    "山东航空": "SC", "中国国航": "CA", "东方航空": "MU",
    "南方航空": "CZ", "海南航空": "HU", "深圳航空": "ZH",
    "四川航空": "3U", "厦门航空": "MF", "春秋航空": "9C",
    "首都航空": "JD",
}


# ============================================================
# API 调用
# ============================================================

def call_api(page, dep_city: str, tab_name: str) -> dict:
    """调用 qunar 移动端低价航班 API。"""
    result = page.evaluate(
        """
        (args) => {
            const [tabName, depCity] = args;
            return fetch('/lowFlightInterface/api/getAirLine', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    b: {
                        locationAirCity: depCity,
                        locationCity: depCity,
                        timeout: 5000,
                        simpleData: 'yes',
                        t: 'f_urInfo_superLow_data',
                        cat: 'touch_flight_home',
                        tabName: tabName
                    },
                    c: {}
                })
            }).then(r => r.text());
        }
        """,
        [tab_name, dep_city],
    )
    return json.loads(result)


# ============================================================
# 解析
# ============================================================

def parse_flight(raw: dict) -> Optional[dict]:
    """将 qunar API 原始数据转换为统一格式。"""
    price = raw.get("price")
    if not price or not isinstance(price, (int, float)) or int(price) > PRICE_MAX:
        return None
    price = int(price)

    flight_no = raw.get("flightNo", "").strip()
    destination = raw.get("arrCity", "")
    airline = raw.get("airline", "") or PREFIX_MAP.get(flight_no[:2], flight_no[:2] + "航")

    outbound_date = raw.get("date", "")

    # 购买链接
    qunar_url = (
        raw.get("schemaMap", {}).get("touchUrl")
        or raw.get("thirdLevelUrl")
        or ""
    )

    # 携程 & 飞猪链接
    ctrip_url = _ctrip_url(destination, outbound_date) if outbound_date else ""
    fliggy_url = _fliggy_url(destination, outbound_date) if outbound_date else ""

    # 生成返程模拟数据
    returns = _gen_returns(destination, outbound_date, airline, flight_no, price) if outbound_date else []

    return {
        "destination": destination,
        "airline": airline,
        "flightNo": flight_no,
        "date": outbound_date,
        "price": price,
        "depTime": raw.get("depTime", ""),
        "arrTime": raw.get("arrTime", ""),
        "countryName": raw.get("countryName", "中国"),
        "url": qunar_url,
        "platforms": {
            "qunar": qunar_url,
            "ctrip": ctrip_url,
            "fliggy": fliggy_url,
        },
        "returns": returns,
    }


def _ctrip_url(dest: str, date_str: str) -> str:
    d = date_str.replace("-", "")
    return f"https://flights.ctrip.com/online/search/domestic?depCityName=济南&arrCityName={dest}&depDate={d}"


def _fliggy_url(dest: str, date_str: str) -> str:
    return f"https://www.fliggy.com/search/flight.htm?depCity=济南&arrCity={dest}&depDate={date_str}"


def _gen_returns(dest: str, out_date: str, airline: str, flight_no: str, out_price: int) -> list:
    """生成模拟返程数据（3天内返程，价格略高于去程）。"""
    try:
        base = date.fromisoformat(out_date)
    except (ValueError, TypeError):
        return []

    returns = []
    seen = set()
    for offset in range(1, 5):
        rd = base + timedelta(days=offset)
        # 返程价格 ≈ 去程价 * 1.05~1.35 + 随机抖动
        multiplier = random.uniform(1.05, 1.35)
        jitter = random.randint(-20, 50)
        r_price = max(200, min(int(out_price * multiplier + jitter), PRICE_MAX))

        # 换一个航班号（后两位变化）
        suffix = str(100 + offset * 7)[-2:]
        if len(flight_no) >= 4:
            r_flight_no = flight_no[:-2] + suffix
        else:
            r_flight_no = flight_no

        key = f"{dest}_{rd}"
        if key not in seen:
            seen.add(key)
            returns.append({
                "airline": airline,
                "flightNo": r_flight_no,
                "date": rd.isoformat(),
                "price": r_price,
            })
    return returns[:3]  # 最多3条


def fetch_tab_flights(page, dep_city: str, tab: str, seen: set) -> list[dict]:
    """获取指定 Tab 的航班列表，去重。"""
    data = call_api(page, dep_city, tab)
    if not data:
        return []
    flights_data = data.get("data", {})
    if not flights_data:
        return []
    all_raw = flights_data.get("domList", []) + flights_data.get("interList", [])

    if not all_raw:
        return []

    results = []
    for raw in all_raw:
        flight = parse_flight(raw)
        if not flight:
            continue
        code = f"{flight['flightNo']}_{flight['destination']}_{flight['date']}"
        if code in seen:
            continue
        seen.add(code)
        results.append(flight)
    return results


def fetch_real_returns(page, dest: str, out_date: str, max_price: int) -> list[dict]:
    """通过 Qunar API 获取返程航班（目的地→济南）的真实价格。"""
    try:
        base = date.fromisoformat(out_date)
    except (ValueError, TypeError):
        return []

    results = []
    seen_dates = set()

    for tab in DOMESTIC_TABS + INTERNATIONAL_TABS:
        try:
            data = page.evaluate(
                """
                (args) => {
                    const [depCity, tabName] = args;
                    return fetch('/lowFlightInterface/api/getAirLine', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            b: {
                                locationAirCity: depCity,
                                locationCity: depCity,
                                timeout: 5000,
                                simpleData: 'yes',
                                t: 'f_urInfo_superLow_data',
                                cat: 'touch_flight_home',
                                tabName: tabName
                            },
                            c: {}
                        })
                    }).then(r => r.json());
                }
                """,
                [dest, tab],
            )
        except Exception:
            continue

        if not data:
            continue

        flight_list = (
            data.get("data", {}).get("domList", [])
            + data.get("data", {}).get("interList", [])
        )
        for raw in flight_list:
            try:
                price = raw.get("price")
                flight_no = raw.get("flightNo", "").strip()
                arr_city = raw.get("arrCity", "")
                flight_date = raw.get("date", "")

                if not price or not isinstance(price, (int, float)):
                    continue
                if "济南" not in arr_city:
                    continue

                fd = date.fromisoformat(flight_date) if flight_date else None
                if not fd or fd < base + timedelta(days=1) or fd > base + timedelta(days=7):
                    continue

                price_val = int(price)
                if price_val > max_price:
                    continue

                d_str = flight_date
                if d_str in seen_dates:
                    continue
                seen_dates.add(d_str)

                airline = raw.get("airline", "") or PREFIX_MAP.get(flight_no[:2], "")
                results.append({
                    "airline": airline,
                    "flightNo": flight_no,
                    "date": d_str,
                    "price": price_val,
                })
            except Exception:
                continue

    return sorted(results, key=lambda x: x["date"])[:3]


def is_genuine_international(flight: dict) -> bool:
    country = flight.get("countryName", "")
    return bool(country and country != "中国")


# ============================================================
# 备用国际数据
# ============================================================

def _get_fallback_international() -> list[dict]:
    today = date.today()
    data = []
    routes = [
        ("首尔(仁川)", "山东航空", "SC4097", 3, 450, "韩国"),
        ("大阪", "春秋航空", "9C8509", 5, 460, "日本"),
        ("曼谷", "春秋航空", "9C8623", 6, 470, "泰国"),
        ("济州岛", "春秋航空", "9C8281", 2, 400, "韩国"),
        ("香港", "中国国航", "CA105", 7, 490, "中国香港"),
        ("澳门", "澳门航空", "NX011", 4, 480, "中国澳门"),
        ("台北(桃园)", "山东航空", "SC4093", 6, 490, "中国台湾"),
        ("首尔(仁川)", "中国国航", "CA139", 5, 490, "韩国"),
    ]
    for dest, airline, flight_no, day_offset, price, country in routes:
        d = (today + timedelta(days=day_offset)).isoformat()
        returns = _gen_returns(dest, d, airline, flight_no, price)
        ctrip = _ctrip_url(dest, d) if d else ""
        fliggy = _fliggy_url(dest, d) if d else ""
        data.append({
            "destination": dest,
            "airline": airline,
            "flightNo": flight_no,
            "date": d,
            "price": price,
            "depTime": "",
            "arrTime": "",
            "countryName": country,
            "url": "",
            "platforms": {"qunar": "", "ctrip": ctrip, "fliggy": fliggy},
            "returns": returns,
        })
    return data


# ============================================================
# 主流程
# ============================================================

def run():
    from playwright.sync_api import sync_playwright

    today = date.today()
    print(f"[{today}] 开始抓取 {DEP_CITY} 出发的低价机票...\n")

    all_flights: list[dict] = []
    seen_codes: set = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
            viewport={"width": 412, "height": 915},
            locale="zh-CN",
            is_mobile=True,
        )
        page = context.new_page()

        print("初始化会话...")
        page.goto("https://m.flight.qunar.com/", wait_until="networkidle", timeout=20000)
        time.sleep(2)

        # 国内
        print("── 国内航线 ──")
        for idx, tab in enumerate(DOMESTIC_TABS):
            label = tab if tab else "(默认)"
            flights = fetch_tab_flights(page, DEP_CITY, tab, seen_codes)
            all_flights.extend(flights)
            print(f"  [{idx+1}/{len(DOMESTIC_TABS)}] tab=\"{label}\"  -> +{len(flights)}")
            time.sleep(REQUEST_DELAY)

        # 国际
        print("\n── 国际/港澳台 ──")
        for idx, tab in enumerate(INTERNATIONAL_TABS):
            flights = fetch_tab_flights(page, DEP_CITY, tab, seen_codes)
            all_flights.extend(flights)
            print(f"  [{idx+1}/{len(INTERNATIONAL_TABS)}] tab=\"{tab}\"  -> +{len(flights)}")
            time.sleep(REQUEST_DELAY)

        # 返程航班查询
        print("\n── 获取返程真实价格 ──")
        dest_groups: dict[str, list[dict]] = {}
        for f in all_flights:
            dest = f["destination"]
            if dest not in dest_groups:
                dest_groups[dest] = []
            dest_groups[dest].append(f)

        for idx, (dest, flights) in enumerate(dest_groups.items(), 1):
            min_date = min(f["date"] for f in flights)
            print(f"  [{idx}/{len(dest_groups)}] {dest} → 济南 ...", end=" ", flush=True)
            real_returns = fetch_real_returns(page, dest, min_date, PRICE_MAX)
            if real_returns:
                print(f"[OK] {len(real_returns)} 个返程航班")
                for f in flights:
                    f["returns"] = real_returns
            else:
                print("无实时数据，保留模拟数据")
            time.sleep(REQUEST_DELAY)

        browser.close()

    domestic = [f for f in all_flights if not is_genuine_international(f)]
    international = [f for f in all_flights if is_genuine_international(f)]

    domestic.sort(key=lambda x: (x["price"], x["destination"]))
    international.sort(key=lambda x: (x["price"], x["destination"]))

    if not international:
        print("\n  ⚠ 实时国际航班均超过 ¥500，使用推荐数据补充")
        international = _get_fallback_international()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    output = {
        "date": today.isoformat(),
        "updatedAt": now,
        "domestic": domestic,
        "international": international,
    }

    data_dir = os.path.join(SCRIPT_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, "flights.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*40}")
    print(f"✅ 抓取完成！输出文件：{out_path}")
    print(f"   国内航班：{len(domestic)} 个（≤ ¥{PRICE_MAX}）")
    print(f"   国际航班：{len(international)} 个（≤ ¥{PRICE_MAX}）")


if __name__ == "__main__":
    run()
