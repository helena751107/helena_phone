# 1.4 Git/GitHub 연결

> 폰에서 작업한 코드를 GitHub에 저장하는 방법

## 설정

```bash
# Git 사용자 정보
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# 저장소 클론
git clone https://github.com/사용자명/레포명.git
cd 레포명
```

## 매일 쓰는 명령어

```bash
# 상태 확인
git status
git log --oneline -5

# 변경 저장
git add -A
git commit -m "작업 내용"
git push
```

## 여러 레포 관리

5개 레포를 운영한다면 각각 remote 설정:

```bash
git remote -v
# origin → https://github.com/사용자명/helena_phone.git

# 다른 레포도 동일한 방식
git clone https://github.com/사용자명/helana_log.git
git clone https://github.com/사용자명/helana-faith.git
```

## .gitignore 필수

```gitignore
.secrets.env
node_modules/
__pycache__/
*.log
```

> `.secrets.env`는 **절대 git에 올리면 안 됨** — 토큰/비번이 다 들어있음.
