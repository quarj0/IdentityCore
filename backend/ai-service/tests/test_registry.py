from app.document_classification.registry import list_definitions


def test_enabled_country_passport_candidates_participate():
    ng = list_definitions("NG")
    sn = list_definitions("SN")
    tg = list_definitions("TG")
    ci = list_definitions("CI")

    assert any(definition.definition_id == "ng.passport.candidate.v1" for definition in ng)
    assert any(definition.definition_id == "sn.passport.candidate.v1" for definition in sn)
    assert any(definition.definition_id == "tg.passport.candidate.v1" for definition in tg)
    assert any(definition.definition_id == "ci.passport.candidate.v1" for definition in ci)


def test_registry_respects_enabled_country_config(monkeypatch):
    class FakeSettings:
        document_classification_enabled_country_codes = ("GH",)

    monkeypatch.setattr("app.document_classification.registry._get_settings", lambda: FakeSettings())

    gh_definitions = list_definitions("GH")
    ng_definitions = list_definitions("NG")

    assert any(definition.country_code == "GH" for definition in gh_definitions if definition.country_code)
    assert all(definition.country_code != "NG" for definition in ng_definitions if definition.country_code)
