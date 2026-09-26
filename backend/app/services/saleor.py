import httpx
from app.config import settings

PRODUCT_FIELDS = '''
id
name
slug
description
category { name }
thumbnail { url alt }
pricing { priceRange { start { gross { amount currency } } } }
'''

async def saleor_request(query: str, variables: dict):
    headers = {"Content-Type": "application/json"}
    if settings.saleor_token:
        headers["Authorization"] = f"Bearer {settings.saleor_token}"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(settings.saleor_api_url, json={"query": query, "variables": variables}, headers=headers)
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            raise RuntimeError(payload["errors"])
        return payload.get("data", {})

async def get_product(product_id: str | None):
    if not product_id:
        return None
    query = f'''query Product($id: ID!, $channel: String!) {{
      product(id: $id, channel: $channel) {{ {PRODUCT_FIELDS} }}
    }}'''
    data = await saleor_request(query, {"id": product_id, "channel": settings.saleor_channel})
    return data.get("product")

async def get_products(search: str = "", limit: int = 24):
    query = f'''query Products($channel: String!, $first: Int!, $search: String) {{
      products(first: $first, channel: $channel, filter: {{search: $search}}) {{
        edges {{ node {{ {PRODUCT_FIELDS} }} }}
      }}
    }}'''
    data = await saleor_request(query, {"channel": settings.saleor_channel, "first": limit, "search": search or None})
    return [x["node"] for x in data.get("products", {}).get("edges", [])]
