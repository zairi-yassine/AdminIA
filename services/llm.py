# services/llm.py
# Ce fichier gère tous les appels au LLM via OpenRouter.
# OpenRouter = accès unifié à des dizaines de modèles gratuits.

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # charge le fichier .env

class LLMService:

    def __init__(self):
        # OpenAI client pointant vers OpenRouter
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",  # <- seul changement vs OpenAI
        )
        # Modèles gratuits recommandés sur OpenRouter :
        # "mistralai/mistral-7b-instruct"       ← très bon en français
        # "meta-llama/llama-3-8b-instruct"      ← rapide et précis  
        # "google/gemma-3-12b-it:free"          ← excellent, gratuit
        self.model = "mistralai/mistral-7b-instruct"

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