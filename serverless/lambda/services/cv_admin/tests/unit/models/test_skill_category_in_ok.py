"""SkillCategoryIn acepta el shape del seed (skills ordenadas + kind).

Given un payload de categoria de skills,
When se valida con SkillCategoryIn,
Then pasa y conserva el ORDEN de skills.
"""


def test_skill_category_in_ok():
    from models.content import SkillCategoryIn

    payload = {
        'slug': 'ai-workflows',
        'name': {'es': 'AI Workflows', 'en': 'AI Workflows'},
        'kind': 'technical',
        'skills': ['Claude Code', 'Cursor', 'MCP Servers'],
        'niches': ['vibe', 'generic'],
        '_meta': {},
    }

    model = SkillCategoryIn.model_validate(payload)

    assert model.kind == 'technical'
    assert model.skills == ['Claude Code', 'Cursor', 'MCP Servers']
