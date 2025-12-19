# {{ nome }}

Tiri Salvezza:** Temp {{ salvezze.Tempra }} / Riflessi {{ salvezze.Riflessi }} / Volontà {{ salvezze['Volontà'] }}

**BAB:** {{ BAB }} | **Iniziativa:** {{ iniziativa }} | **Velocità:** {{ velocita }}

Statistiche:
{% for label, key in [
    ("For", "FOR"),
    ("Des", "DES"),
    ("Cos", "COS"),
    ("Int", "INT"),
    ("Sag", "SAG"),
    ("Car", "CAR"),
] %}
**{{ label }}** {{ statistiche[key] }} (mod {{ (statistiche[key] - 10) // 2 }})
{% endfor %}

{% if skills %}
Competenze:
{% for skill in skills %}- {{ skill.get('nome') or skill.get('name') }}
{% endfor %}
{% endif %}

{% if equipaggiamento %}
Equipaggiamento:
{% for item in equipaggiamento %}- {{ item }}
{% endfor %}
{% endif %}

{% set ledger_entries = ledger_movimenti or (ledger.movimenti if ledger else []) %}
{% if ledger_entries %}
Ledger:
{% for mov in ledger_entries %}- {{ mov.get('voce') or mov.get('oggetto') or mov.get('label') or mov.get('categoria') }}
{% endfor %}
{% endif %}
