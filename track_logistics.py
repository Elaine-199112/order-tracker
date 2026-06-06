#!/usr/bin/env python3
"""
快递100物流追踪脚本
读取 orders.json，查询有快递单号的订单，更新物流状态
"""
import json, hashlib, urllib.request, urllib.parse, os, sys

ORDERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orders.json")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kuaidi100_config.json")

API_URL = "https://poll.kuaidi100.com/poll/query.do"

# Status mapping: kuaidi100 status code → Chinese description
STATUS_MAP = {
    "0": "在途",
    "1": "已揽收",
    "2": "疑难",
    "3": "已签收",
    "4": "退签",
    "5": "同城派送中",
    "6": "退回",
    "7": "转单",
    "10": "待清关",
    "11": "清关中",
    "12": "已清关",
    "13": "清关异常",
    "14": "拒签"
}

def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

def load_orders():
    with open(ORDERS_FILE) as f:
        return json.load(f)

def save_orders(data):
    with open(ORDERS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def query_kuaidi100(customer, key, carrier, tracking_num):
    """Query kuaidi100 for tracking info"""
    param = json.dumps({"com": carrier, "num": tracking_num})
    sign_raw = param + key + customer
    sign = hashlib.md5(sign_raw.encode()).hexdigest().upper()
    
    post_data = urllib.parse.urlencode({
        "customer": customer,
        "sign": sign,
        "param": param
    }).encode()
    
    req = urllib.request.Request(API_URL, data=post_data)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        return result
    except Exception as e:
        return {"error": str(e)}

def main():
    config = load_config()
    data = load_orders()
    
    updated_count = 0
    
    for oid, order in data["orders"].items():
        tracking_num = order.get("tracking_number", "").strip()
        carrier = order.get("carrier", "").strip()
        
        # Skip orders without tracking or already delivered
        if not tracking_num or not carrier:
            continue
        
        # Skip if already signed
        if order.get("tracking_status") == "已签收":
            continue
        
        print(f"Querying {oid}: {carrier} {tracking_num}...")
        result = query_kuaidi100(config["customer"], config["key"], carrier, tracking_num)
        
        if "error" in result:
            print(f"  ⚠️ Error: {result['error']}")
            continue
        
        if result.get("returnCode") != "200":
            print(f"  ⚠️ API error: {result.get('message', 'unknown')}")
            continue
        
        # Parse tracking data
        traces = result.get("data", [])
        state = result.get("state", "")
        status_text = STATUS_MAP.get(state, state)
        
        # Update order
        order["tracking_status"] = status_text
        order["tracking_ischeck"] = result.get("ischeck", "")
        
        # Build tracking history
        tracking_history = []
        for trace in reversed(traces):  # Reverse to get chronological order
            tracking_history.append({
                "time": trace.get("ftime", ""),
                "desc": trace.get("context", "")
            })
        
        order["tracking_history"] = tracking_history
        
        # Update order updates if status changed
        existing_notes = {u.get("note", "") for u in order.get("updates", [])}
        new_note = f"📦 {status_text} - {traces[0].get('context', '')[:50]}" if traces else f"📦 {status_text}"
        
        if new_note not in existing_notes and status_text:
            order.setdefault("updates", []).append({
                "date": traces[0].get("ftime", "")[:10] if traces else "",
                "stage_key": "shipping",
                "note": new_note
            })
        
        print(f"  ✅ Status: {status_text} ({len(traces)} trace points)")
        updated_count += 1
    
    if updated_count > 0:
        save_orders(data)
        print(f"\n✅ Updated {updated_count} order(s)")
    else:
        print("\nNo orders to update")

if __name__ == "__main__":
    main()
