"""팀/선수 별칭 데이터 — 알고리즘이 아니라 순수 데이터라 analysis/ 밖(backend/youtube.py와
같은 층위)에 둔다. 새 선수·팀이 생기면 이 파일에만 한 줄 추가하면 되고, 이 데이터를
실제로 어떻게 쓰는지는 analysis/aliases.py의 normalize_aliases()가 담당한다."""

TEAM_ALIASES = {
    # T1
    "t1": "TEAM_T1",
    "티원": "TEAM_T1",
    "skt": "TEAM_T1",
    "sk telecom t1": "TEAM_T1",
    "skt t1": "TEAM_T1",

    # Hanwha Life Esports
    "hle": "TEAM_HLE",
    "hanwha life esports": "TEAM_HLE",
    "hanwha life": "TEAM_HLE",
    "한화생명e스포츠": "TEAM_HLE",
    "한화생명": "TEAM_HLE",
    "한화": "TEAM_HLE",

    # Gen.G
    "gen.g": "TEAM_GENG",
    "geng": "TEAM_GENG",
    "gen": "TEAM_GENG",
    "젠지": "TEAM_GENG",

    # Dplus KIA
    "dk": "TEAM_DK",
    "dplus kia": "TEAM_DK",
    "dplus": "TEAM_DK",
    "디플러스 기아": "TEAM_DK",
    "디플러스": "TEAM_DK",
    "딮기": "TEAM_DK",
    "담원": "TEAM_DK",
    "담원기아": "TEAM_DK",

    # KT Rolster
    "kt": "TEAM_KT",
    "kt rolster": "TEAM_KT",
    "케이티": "TEAM_KT",
    "kt 롤스터": "TEAM_KT",
    "킅": "TEAM_KT",

    # BNK FEARX
    "bfx": "TEAM_BFX",
    "bnk fearx": "TEAM_BFX",
    "fearx": "TEAM_BFX",
    "피어엑스": "TEAM_BFX",
    "bnk 피어엑스": "TEAM_BFX",

    # DN SOOPers
    "dns": "TEAM_DNS",
    "dn soopers": "TEAM_DNS",
    "soopers": "TEAM_DNS",
    "dn 수퍼스": "TEAM_DNS",
    "수퍼스": "TEAM_DNS",
    "dnf": "TEAM_DNS",  # 예전 표기/오타 대비용

    # HANJIN BRION
    "bro": "TEAM_BRO",
    "brion": "TEAM_BRO",
    "hanjin brion": "TEAM_BRO",
    "한진 브리온": "TEAM_BRO",
    "브리온": "TEAM_BRO",

    # Kiwoom DRX
    "krx": "TEAM_KRX",
    "drx": "TEAM_KRX",
    "kiwoom drx": "TEAM_KRX",
    "키움 drx": "TEAM_KRX",
    "키움디알엑스": "TEAM_KRX",
    "디알엑스": "TEAM_KRX",

    # Nongshim RedForce
    "ns": "TEAM_NS",
    "nongshim redforce": "TEAM_NS",
    "nongshim": "TEAM_NS",
    "redforce": "TEAM_NS",
    "농심 레드포스": "TEAM_NS",
    "농심": "TEAM_NS",
    "레드포스": "TEAM_NS",
}

# 공식 표기(본명, 영문/한글 게이머 태그) — 확실한 것만. 팬 별명은 별도 FAN_ALIASES에서 관리
OFFICIAL_ALIASES = {
    # HLE
    "zeus": "PLAYER_ZEUS",
    "제우스": "PLAYER_ZEUS",
    "최우제": "PLAYER_ZEUS",
    "우제": "PLAYER_ZEUS",

    "kanavi": "PLAYER_KANAVI",
    "카나비": "PLAYER_KANAVI",
    "서진혁": "PLAYER_KANAVI",
    "진혁": "PLAYER_KANAVI",

    "zeka": "PLAYER_ZEKA",
    "제카": "PLAYER_ZEKA",
    "김건우": "PLAYER_ZEKA",
    "건우": "PLAYER_ZEKA",

    "gumayusi": "PLAYER_GUMAYUSI",
    "guma": "PLAYER_GUMAYUSI",
    "구마유시": "PLAYER_GUMAYUSI",
    "구마": "PLAYER_GUMAYUSI",
    "이민형": "PLAYER_GUMAYUSI",
    "민형": "PLAYER_GUMAYUSI",

    "delight": "PLAYER_DELIGHT",
    "딜라이트": "PLAYER_DELIGHT",
    "유환중": "PLAYER_DELIGHT",
    "환중": "PLAYER_DELIGHT",

    "bluffing": "PLAYER_BLUFFING",
    "블러핑": "PLAYER_BLUFFING",
    "박규용": "PLAYER_BLUFFING",
    "규용": "PLAYER_BLUFFING",

    # T1
    "doran": "PLAYER_DORAN",
    "도란": "PLAYER_DORAN",
    "최현준": "PLAYER_DORAN",

    "oner": "PLAYER_ONER",
    "오너": "PLAYER_ONER",
    "문현준": "PLAYER_ONER",

    "faker": "PLAYER_FAKER",
    "페이커": "PLAYER_FAKER",
    "이상혁": "PLAYER_FAKER",
    "상혁": "PLAYER_FAKER",

    "peyz": "PLAYER_PEYZ",
    "페이즈": "PLAYER_PEYZ",
    "김수환": "PLAYER_PEYZ",
    "수환": "PLAYER_PEYZ",

    "keria": "PLAYER_KERIA",
    "케리아": "PLAYER_KERIA",
    "류민석": "PLAYER_KERIA",
    "민석": "PLAYER_KERIA",

    # Gen.G
    "kiin": "PLAYER_KIIN",
    "기인": "PLAYER_KIIN",
    "김기인": "PLAYER_KIIN",

    "canyon": "PLAYER_CANYON",
    "캐니언": "PLAYER_CANYON",
    "김건부": "PLAYER_CANYON",
    "건부": "PLAYER_CANYON",

    "chovy": "PLAYER_CHOVY",
    "쵸비": "PLAYER_CHOVY",
    "정지훈": "PLAYER_CHOVY",
    "지훈": "PLAYER_CHOVY",

    "ruler": "PLAYER_RULER",
    "룰러": "PLAYER_RULER",
    "박재혁": "PLAYER_RULER",
    "재혁": "PLAYER_RULER",

    "duro": "PLAYER_DURO",
    "듀로": "PLAYER_DURO",
    "주민규": "PLAYER_DURO",
    "민규": "PLAYER_DURO",

    # Dplus KIA
    "siwoo": "PLAYER_SIWOO",
    "시우": "PLAYER_SIWOO",
    "전시우": "PLAYER_SIWOO",

    "lucid": "PLAYER_LUCID",
    "루시드": "PLAYER_LUCID",
    "최용혁": "PLAYER_LUCID",
    "용혁": "PLAYER_LUCID",

    "sharvel": "PLAYER_SHARVEL",
    "샤벨": "PLAYER_SHARVEL",
    "김단우": "PLAYER_SHARVEL",
    "단우": "PLAYER_SHARVEL",

    "showmaker": "PLAYER_SHOWMAKER",
    "쇼메이커": "PLAYER_SHOWMAKER",
    "쇼메": "PLAYER_SHOWMAKER",
    "허수": "PLAYER_SHOWMAKER",

    "smash": "PLAYER_SMASH",
    "스매쉬": "PLAYER_SMASH",
    "신금재": "PLAYER_SMASH",
    "금재": "PLAYER_SMASH",

    "career": "PLAYER_CAREER",
    "커리어": "PLAYER_CAREER",
    "오형석": "PLAYER_CAREER",
    "형석": "PLAYER_CAREER",

    # KT
    "perfect": "PLAYER_PERFECT",
    "퍼펙트": "PLAYER_PERFECT",
    "이승민": "PLAYER_PERFECT",
    "승민": "PLAYER_PERFECT",

    "cuzz": "PLAYER_CUZZ",
    "커즈": "PLAYER_CUZZ",
    "문우찬": "PLAYER_CUZZ",
    "우찬": "PLAYER_CUZZ",

    "bdd": "PLAYER_BDD",
    "비디디": "PLAYER_BDD",
    "곽보성": "PLAYER_BDD",
    "보성": "PLAYER_BDD",

    "aiming": "PLAYER_AIMING",
    "에이밍": "PLAYER_AIMING",
    "김하람": "PLAYER_AIMING",
    "하람": "PLAYER_AIMING",

    "fenrir": "PLAYER_FENRIR",
    "펜리르": "PLAYER_FENRIR",
    "박강준": "PLAYER_FENRIR",
    "강준": "PLAYER_FENRIR",

    "effort": "PLAYER_EFFORT",
    "에포트": "PLAYER_EFFORT",
    "이상호": "PLAYER_EFFORT",
    "상호": "PLAYER_EFFORT",

    # NS
    "kingen": "PLAYER_KINGEN",
    "킹겐": "PLAYER_KINGEN",
    "황성훈": "PLAYER_KINGEN",

    "sponge": "PLAYER_SPONGE",
    "스폰지": "PLAYER_SPONGE",
    "배영준": "PLAYER_SPONGE",
    "영준": "PLAYER_SPONGE",

    "scout": "PLAYER_SCOUT",
    "스카웃": "PLAYER_SCOUT",
    "이예찬": "PLAYER_SCOUT",
    "예찬": "PLAYER_SCOUT",

    "lehends": "PLAYER_LEHENDS",
    "리헨즈": "PLAYER_LEHENDS",
    "손시우": "PLAYER_LEHENDS",

    "pleata": "PLAYER_PLEATA",
    "플레타": "PLAYER_PLEATA",
    "손민우": "PLAYER_PLEATA",
    "민우": "PLAYER_PLEATA",

    "taeyoon": "PLAYER_TAEYOON",
    "태윤": "PLAYER_TAEYOON",
    "김태윤": "PLAYER_TAEYOON",

    "diable": "PLAYER_DIABLE",
    "디아블": "PLAYER_DIABLE",
    "남대근": "PLAYER_DIABLE",
    "대근": "PLAYER_DIABLE",

    # BNK FEARX
    "clear": "PLAYER_CLEAR",
    "클리어": "PLAYER_CLEAR",
    "송현민": "PLAYER_CLEAR",
    "현민": "PLAYER_CLEAR",

    "raptor": "PLAYER_RAPTOR",
    "랩터": "PLAYER_RAPTOR",
    "전어진": "PLAYER_RAPTOR",
    "어진": "PLAYER_RAPTOR",

    "vicla": "PLAYER_VICLA",
    "빅라": "PLAYER_VICLA",
    "이대광": "PLAYER_VICLA",
    "대광": "PLAYER_VICLA",

    "daystar": "PLAYER_DAYSTAR",
    "데이스타": "PLAYER_DAYSTAR",
    "유지명": "PLAYER_DAYSTAR",
    "지명": "PLAYER_DAYSTAR",

    "slayer": "PLAYER_SLAYER",
    "슬레이어": "PLAYER_SLAYER",
    "김진영": "PLAYER_SLAYER",
    "진영": "PLAYER_SLAYER",

    "kellin": "PLAYER_KELLIN",
    "켈린": "PLAYER_KELLIN",
    "김형규": "PLAYER_KELLIN",
    "형규": "PLAYER_KELLIN",

    # DN SOOPers
    "dudu": "PLAYER_DUDU",
    "두두": "PLAYER_DUDU",
    "이동주": "PLAYER_DUDU",
    "동주": "PLAYER_DUDU",

    "pyosik": "PLAYER_PYOSIK",
    "표식": "PLAYER_PYOSIK",
    "홍창현": "PLAYER_PYOSIK",
    "창현": "PLAYER_PYOSIK",

    "ddoiv": "PLAYER_DDOIV",
    "또이브": "PLAYER_DDOIV",
    "방문영": "PLAYER_DDOIV",
    "문영": "PLAYER_DDOIV",

    "clozer": "PLAYER_CLOZER",
    "클로저": "PLAYER_CLOZER",
    "이주현": "PLAYER_CLOZER",
    "주현": "PLAYER_CLOZER",

    "deokdam": "PLAYER_DEOKDAM",
    "덕담": "PLAYER_DEOKDAM",
    "서대길": "PLAYER_DEOKDAM",
    "대길": "PLAYER_DEOKDAM",

    "enosh": "PLAYER_ENOSH",
    "에노쉬": "PLAYER_ENOSH",
    "곽규준": "PLAYER_ENOSH",
    "규준": "PLAYER_ENOSH",

    "peter": "PLAYER_PETER",
    "피터": "PLAYER_PETER",
    "정윤수": "PLAYER_PETER",
    "윤수": "PLAYER_PETER",

    "life": "PLAYER_LIFE",
    "라이프": "PLAYER_LIFE",
    "김정민": "PLAYER_LIFE",
    "정민": "PLAYER_LIFE",

    "quantum": "PLAYER_QUANTUM",
    "퀀텀": "PLAYER_QUANTUM",
    "손정환": "PLAYER_QUANTUM",
    "정환": "PLAYER_QUANTUM",

    # BRO
    "casting": "PLAYER_CASTING",
    "캐스팅": "PLAYER_CASTING",
    "신민제": "PLAYER_CASTING",
    "민제": "PLAYER_CASTING",

    "gideon": "PLAYER_GIDEON",
    "기드온": "PLAYER_GIDEON",
    "김민성": "PLAYER_GIDEON",
    "민성": "PLAYER_GIDEON",

    "loki": "PLAYER_LOKI",
    "로키": "PLAYER_LOKI",
    "이상민": "PLAYER_LOKI",
    "상민": "PLAYER_LOKI",

    "roamer": "PLAYER_ROAMER",
    "로머": "PLAYER_ROAMER",
    "조우진": "PLAYER_ROAMER",
    "우진": "PLAYER_ROAMER",

    "teddy": "PLAYER_TEDDY",
    "테디": "PLAYER_TEDDY",
    "박진성": "PLAYER_TEDDY",
    "진성": "PLAYER_TEDDY",

    "namgung": "PLAYER_NAMGUNG",
    "남궁": "PLAYER_NAMGUNG",
    "남궁성훈": "PLAYER_NAMGUNG",

    # KRX
    "rich": "PLAYER_RICH",
    "리치": "PLAYER_RICH",
    "이재원": "PLAYER_RICH",
    "재원": "PLAYER_RICH",

    "willer": "PLAYER_WILLER",
    "윌러": "PLAYER_WILLER",
    "김정현": "PLAYER_WILLER",
    "정현": "PLAYER_WILLER",

    "ucal": "PLAYER_UCAL",
    "유칼": "PLAYER_UCAL",
    "손우현": "PLAYER_UCAL",
    "우현": "PLAYER_UCAL",

    "jiwoo": "PLAYER_JIWOO",
    "지우": "PLAYER_JIWOO",
    "정지우": "PLAYER_JIWOO",

    "lazyfeel": "PLAYER_LAZYFEEL",
    "레이지필": "PLAYER_LAZYFEEL",
    "trần bảo minh": "PLAYER_LAZYFEEL",
    "tran bao minh": "PLAYER_LAZYFEEL",

    "andil": "PLAYER_ANDIL",
    "안딜": "PLAYER_ANDIL",
    "문관빈": "PLAYER_ANDIL",
    "관빈": "PLAYER_ANDIL",
}

# 팬들이 실제로 댓글/제목에 쓰는 비공식 별명. 처음부터 완벽하게 채우려 하지 않고,
# 분석 결과에서 자주 보이는 미등록 별명을 발견할 때마다 여기에 한 줄씩 추가하는 방식으로 운영
FAN_ALIASES = {
    "구마": "PLAYER_GUMAYUSI",
    "우둥이": "PLAYER_ZEUS",
    "러핑이": "PLAYER_BLUFFING",
    "러핑": "PLAYER_BLUFFING",
    "대상혁": "PLAYER_FAKER",
    "갓상혁": "PLAYER_FAKER",
    "우리혁": "PLAYER_FAKER",
    "우리진혁": "PLAYER_KANAVI",
}
