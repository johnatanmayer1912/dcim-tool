import yaml, os, sys
path = 'policies/standards.yaml'
print(f'File size: {os.path.getsize(path)} bytes')
with open(path, encoding='utf-8') as f:
    data = yaml.safe_load(f)
policies = data.get('policies', [])
print(f'Policies loaded: {len(policies)}')
if policies:
    print(f'First policy id: {policies[0].get("id")}')
    print(f'Last policy id: {policies[-1].get("id")}')
    cats = sorted(set(p.get('category','?') for p in policies))
    print(f'Categories: {cats}')
else:
    print('NO POLICIES FOUND')
    with open(path, encoding='utf-8') as f:
        content = f.read()
    idx = content.find('policies:')
    print(f'policies: key at index {idx}')
    print(f'Content after policies: key: {repr(content[idx:idx+300])}')
