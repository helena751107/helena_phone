# phone-mcp-server

> Claude Code가 폰 하드웨어를 다루는 MCP 서버

## 구조
```
Claude Code → MCP HTTP :3456 → phone-mcp-server → termux-* → 하드웨어
```

## 관련
- [phone-MCP 18도구](../_notebook/10-phone-mcp.md)
- [phone-health](../phone-health.sh)
- [Termux:API](./termux-api.md)

## 시작
```bash
bash /root/work/phone-mcp.sh --port 3456
```
