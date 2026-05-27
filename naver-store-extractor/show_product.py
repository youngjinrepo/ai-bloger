import json

with open('output/2849385212/2849385212_product.json', 'rb') as f:
    data = json.load(f)

# 전체 키 구조 탐색
def show_keys(obj, prefix='', depth=0):
    if depth > 3:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            print(f"{'  '*depth}{prefix}{k}: {type(v).__name__}", end='')
            if isinstance(v, (str, int, float, bool)) and not isinstance(v, bool):
                print(f" = {str(v)[:80]}")
            else:
                print()
            if isinstance(v, (dict, list)):
                show_keys(v, '', depth+1)
    elif isinstance(obj, list) and obj:
        print(f"{'  '*depth}[list len={len(obj)}]")
        show_keys(obj[0], '', depth+1)

show_keys(data)
