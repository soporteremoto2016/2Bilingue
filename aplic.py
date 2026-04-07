# ---------------- PROCESAR MENSAJE ----------------

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Lucy está pensando..."):

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": f"Topic: {st.session_state.topic}"}
            ] + st.session_state.messages

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )

            reply = response.choices[0].message.content
            st.write(reply)

            # 🔊 AUDIO
            audio_response = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=reply
            )

            st.audio(audio_response.content, format="audio/mp3")

            st.session_state.messages.append({"role": "assistant", "content": reply})

            # Guardar errores
            if "Corrección:" in reply:
                user_data["errores"].append(reply)

            # Evaluación
            if "Evaluación final" in reply:
                stats["conversaciones"] += 1

                import re
                match = re.search(r'Puntuación general: (\d+)', reply)

                if match:
                    score = int(match.group(1))
                    prev = stats["promedio"]
                    n = stats["conversaciones"]

                    stats["promedio"] = int((prev * (n - 1) + score) / n)

                    if score < 40:
                        stats["nivel"] = "A1"
                    elif score < 60:
                        stats["nivel"] = "A2"
                    elif score < 75:
                        stats["nivel"] = "B1"
                    elif score < 90:
                        stats["nivel"] = "B2"
                    else:
                        stats["nivel"] = "C1"

            data[st.session_state.user] = user_data
            save_data(data)
