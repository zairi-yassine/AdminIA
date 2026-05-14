# services/llm.py
# Ce fichier gère les appels au LLM (Ollama, Groq ou OpenRouter).
# Le provider est contrôlé par la variable d'environnement LLM_PROVIDER.

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # charge le fichier .env

class LLMService:

    def __init__(self):
        provider = os.getenv("LLM_PROVIDER").lower()

        if provider == "groq":
            self.client = OpenAI(
                api_key=os.getenv("GROQ_API_KEY"),
                base_url="https://api.groq.com/openai/v1",
            )
            self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        elif provider == "openrouter":
            self.client = OpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            )
            self.model = os.getenv("LLM_MODEL", "google/gemma-4-31b-it:free")
        else:  # ollama (défaut)
            self.client = OpenAI(
                api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
                base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
            )
            self.model = os.getenv("LLM_MODEL", "llama3.2")

    def chat(self, messages: list, system_prompt: str = "") -> str:
        """
        Envoie une conversation au LLM et retourne sa réponse.
        
        messages      = liste de {"role": "user"/"assistant", "content": "..."}
        system_prompt = instructions de comportement pour le LLM
        """
        # Construire la liste complète des messages
        full_messages = []

        # Le system prompt passe en premier si fourni
        if system_prompt:
            full_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Ajouter les messages de la conversation
        full_messages.extend(messages)

        # Appel à l'API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=1000,
            temperature=0.7,   # 0 = réponses déterministes, 1 = créatives
        )

        # Extraire et retourner le texte de la réponse
        return response.choices[0].message.content

    def change_model(self, model_name: str):
        """Permet de changer de modèle facilement."""
        self.model = model_name
        print(f"Modèle changé : {model_name}")
