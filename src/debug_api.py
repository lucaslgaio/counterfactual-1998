"""Diagnóstico da conexão com a API Gemini.

Roda 3 testes em ordem para ajudar a identificar onde está o problema:
  1. Formato e tamanho da API key carregada do .env
  2. Listagem de modelos disponíveis pra essa key
  3. Chamada simples (sem tool use) em gemini-2.0-flash e gemini-1.5-flash

Uso:
    python -m src.debug_api
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from google import genai


def main() -> None:
    load_dotenv()

    key = os.environ.get("GOOGLE_API_KEY", "")
    print("=== 1. API key ===")
    print(f"  tamanho: {len(key)}")
    print(f"  começa com 'AIza': {key.startswith('AIza')}")
    if not key:
        print("\n  ⚠ Sem GOOGLE_API_KEY no .env — adicione antes de continuar.")
        return
    print()

    client = genai.Client(api_key=key)

    print("=== 2. Modelos disponíveis ===")
    try:
        models = list(client.models.list())
        for m in models[:20]:
            print(f"  {m.name}")
        if len(models) > 20:
            print(f"  ... ({len(models) - 20} mais)")
    except Exception as e:
        print(f"  ERRO: {type(e).__name__}: {e}")
        print("\n  → Se for 401/403, a key está inválida ou sem permissão.")
        print("  → Se for outro 4xx, o projeto pode não ter Generative Language API ativada.")
        return
    print()

    candidates = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
    ]
    for i, model_id in enumerate(candidates, start=3):
        print(f"=== {i}. Teste com {model_id} (sem tool use) ===")
        try:
            r = client.models.generate_content(
                model=model_id,
                contents="Diga olá em uma palavra.",
            )
            print(f"  OK: {r.text!r}")
        except Exception as e:
            print(f"  ERRO: {type(e).__name__}: {e}")
        print()

    print("Diagnóstico completo.")


if __name__ == "__main__":
    main()
