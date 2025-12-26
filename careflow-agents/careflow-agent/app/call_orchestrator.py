"""
Call Orchestration Service
Gère l'orchestration des appels entre CareFlow-Main et Twilio-Agent via A2A
"""
import asyncio
from typing import Optional
from datetime import datetime
from google.cloud import firestore

from app.agent import root_agent
from .app_utils.a2a_tools import (
    initiate_call,
    send_instruction_to_patient,
    end_call
)

db = firestore.Client()


async def conduct_patient_call(patient_id: str):
    """
    Orchestre un appel complet avec un patient
    
    Flow:
    1. Récupère context patient depuis Firestore
    2. CareFlow-Main prépare les questions
    3. Initie appel via Twilio-Agent
    4. Boucle conversation avec streaming A2A
    5. CareFlow-Main analyse réponses
    6. Termine appel et enregistre interaction
    
    Args:
        patient_id: ID du patient à appeler
    """
    
    # 1. Récupérer patient context
    patient_ref = db.collection("patients").document(patient_id)
    patient_data = patient_ref.get().to_dict()
    
    phone_number = patient_data.get("contactPhone")
    patient_name = f"{patient_data['firstName']} {patient_data['lastName']}"
    
    # Préparer context médical
    call_context = {
        "diagnosis": patient_data.get("diagnosis"),
        "surgeryDate": patient_data.get("surgeryDate"),
        "medications": patient_data.get("medications", []),
        "lastInteraction": patient_data.get("lastInteractionDate"),
        "symptoms_to_monitor": [
            "douleur thoracique",
            "essoufflement",
            "fièvre",
            "gonflement",
            "nausées"
        ]
    }
    
    print(f"\n{'='*60}")
    print(f"🎯 Appel patient: {patient_name} ({phone_number})")
    print(f"{'='*60}\n")
    
    # 2. CareFlow-Main génère plan d'appel
    planning_prompt = f"""
Prépare un plan d'appel pour le patient {patient_name}.

**Context:**
- Diagnostic: {call_context['diagnosis']}
- Date chirurgie: {call_context['surgeryDate']}
- Médicaments: {', '.join([m['name'] for m in call_context['medications']])}

**Tâche:**
Génère une liste de 3-5 questions à poser au patient, par ordre de priorité.
Format: Questions simples et directes.
"""
    
    planning_response = await root_agent.send_message(planning_prompt)
    questions = planning_response.text.strip().split("\n")
    questions = [q.strip() for q in questions if q.strip() and not q.startswith("#")]
    
    print("📋 Plan d'appel:")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")
    print()
    
    # 3. Initier l'appel via Twilio-Agent
    call_result = await initiate_call(
        phone_number=phone_number,
        patient_name=patient_name,
        patient_id=patient_id,
        call_context=call_context
    )
    
    call_sid = call_result.get("call_sid")
    print(f"📞 Appel initié: {call_sid}\n")
    
    # Attendre que patient décroche (simulé)
    await asyncio.sleep(5)
    print("✅ Patient a décroché\n")
    
    # 4. Boucle conversation
    conversation_history = []
    
    # Message d'accueil
    greeting = f"Bonjour {patient_data['firstName']}, c'est l'infirmière virtuelle de CareFlow Pulse. Je vous appelle pour prendre de vos nouvelles suite à votre opération. Avez-vous quelques minutes ?"
    
    print(f"🤖 Agent → Patient: {greeting}")
    
    async for response_chunk in send_instruction_to_patient(call_sid, greeting):
        if "[TASK COMPLETED" in response_chunk:
            break
        print(f"👤 Patient: {response_chunk}", end="", flush=True)
    
    print("\n")
    
    # Pour chaque question du plan
    for question_num, question in enumerate(questions, 1):
        print(f"\n--- Question {question_num}/{len(questions)} ---")
        print(f"🤖 Agent → Patient: {question}")
        
        patient_response_full = ""
        
        # Streamer la question et recevoir la réponse
        async for response_chunk in send_instruction_to_patient(call_sid, question):
            if "[TASK COMPLETED" in response_chunk:
                break
            patient_response_full += response_chunk
            print(f"👤 Patient: {response_chunk}", end="", flush=True)
        
        print("\n")
        
        # Enregistrer dans historique
        conversation_history.append({
            "agent": question,
            "patient": patient_response_full,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # CareFlow-Main analyse la réponse
        analysis_prompt = f"""
Analyse la réponse du patient à cette question:

**Question:** {question}
**Réponse:** {patient_response_full}

**Context patient:** {call_context}

**Tâche:**
1. Y a-t-il un symptôme préoccupant ? (Oui/Non)
2. Niveau de sévérité: Safe/Warning/Critical
3. Dois-je poser une question de suivi ? (Oui/Non + suggestion)
4. Dois-je terminer l'appel maintenant ? (Oui/Non + raison)

Format:
SYMPTÔME: [Oui/Non]
SÉVÉRITÉ: [Safe/Warning/Critical]
SUIVI: [Oui/Non] - [Question si oui]
TERMINER: [Oui/Non] - [Raison si oui]
"""
        
        analysis = await root_agent.send_message(analysis_prompt)
        analysis_text = analysis.text.strip()
        
        print(f"🧠 Analyse CareFlow-Main:\n{analysis_text}\n")
        
        # Parser décision
        should_terminate = "TERMINER: Oui" in analysis_text or "URGENCE" in analysis_text.upper()
        
        if should_terminate:
            # Alerte critique détectée
            if "Critical" in analysis_text:
                urgent_message = "Je détecte une situation préoccupante. Je vous conseille d'appeler le 15 immédiatement. Un coordinateur va vous rappeler dans les plus brefs délais."
                print(f"🚨 Agent → Patient: {urgent_message}")
                
                async for _ in send_instruction_to_patient(call_sid, urgent_message):
                    pass
            
            break
    
    # 5. Message de clôture
    closing = "Merci pour votre temps. N'hésitez pas à nous appeler si vous avez des questions. Bonne journée !"
    print(f"\n🤖 Agent → Patient: {closing}")
    
    async for _ in send_instruction_to_patient(call_sid, closing):
        pass
    
    # Terminer l'appel
    await end_call(call_sid)
    print(f"\n📞 Appel terminé: {call_sid}\n")
    
    # 6. Génération summary et enregistrement Firestore
    summary_prompt = f"""
Génère un résumé de cet appel patient.

**Patient:** {patient_name}
**Durée:** {len(questions)} questions posées
**Historique conversation:**
{chr(10).join([f"Q: {h['agent']}\nR: {h['patient']}" for h in conversation_history])}

**Tâche:**
Génère:
1. Summary (2-3 phrases)
2. Symptômes signalés
3. Alert nécessaire ? (severity + actions recommandées)
4. Prochaine date de suivi suggérée

Format JSON:
```json
{{
  "summary": "...",
  "symptoms": ["symptom1", "symptom2"],
  "alert": {{
    "needed": true/false,
    "severity": "safe/warning/critical",
    "actions": ["action1", "action2"]
  }},
  "nextFollowUp": "YYYY-MM-DD"
}}
```
"""
    
    summary_response = await root_agent.send_message(summary_prompt)
    summary_json = summary_response.text.strip()
    
    print(f"📊 Summary:\n{summary_json}\n")
    
    # Enregistrer interaction dans Firestore
    interaction_ref = patient_ref.collection("interactions").document()
    interaction_ref.set({
        "timestamp": firestore.SERVER_TIMESTAMP,
        "type": "phone_call",
        "callSid": call_sid,
        "conversationHistory": conversation_history,
        "summary": summary_json,
        "duration": len(questions) * 60,  # Estimation
        "outcome": "completed"
    })
    
    # Si alert nécessaire, créer dans collection /alerts
    # (parsing du JSON et logique d'alert...)
    
    print(f"✅ Interaction enregistrée dans Firestore\n")
    print(f"{'='*60}\n")


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    import asyncio
    
    # Simuler appel d'un patient
    asyncio.run(conduct_patient_call("patient_123"))
