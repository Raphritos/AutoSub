import os
import sys
import subprocess
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import whisper
import srt
from datetime import timedelta
from googletrans import Translator

# --- Configuração da Interface ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class AutoSubApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AutoSub - Automatic Subtitle Generator (v0.4)")
        self.geometry("820x820")
        self.resizable(False, False)

        # Variáveis de estado
        self.caminho_arquivo = ""
        self.pasta_destino = ""
        self.cancelar = False
        self.ultimo_srt = ""
        self.modelo_whisper = None
        self.idioma_interface = "en"  # Padrão: Inglês

        # --- Dicionário de Textos (i18n) ---
        self.textos = {
            "en": {
                "titulo": "AutoSub",
                "subtitulo": "Automatic Subtitle Generator (100% Free)",
                "btn_selecionar": "📂 Select Video/Audio",
                "lbl_arquivo": "No file selected",
                "btn_pasta": "📁 Output Folder",
                "lbl_pasta": "Default folder (same as file)",
                "lbl_idioma": "🌐 Audio Language:",
                "lbl_modelo": "🧠 Whisper Model:",
                "lbl_formato": "📄 Output Format:",
                "chk_traduzir": "Translate to Portuguese (BR)",
                "btn_gerar": "▶ Generate Subtitles",
                "btn_cancelar": "⏹ Cancel",
                "btn_abrir_pasta": "📂 Open Output Folder",
                "status_aguardando": "Waiting...",
                "status_carregar_modelo": "Loading model...",
                "status_transcrever": "Transcribing audio...",
                "status_traduzir": "Translating...",
                "status_gerar": "Generating subtitles...",
                "status_concluido": "Completed!",
                "msg_sucesso": "Subtitles generated successfully!\n\nSaved at:\n",
                "msg_erro": "An error occurred:\n",
                "msg_aviso_arquivo": "Please select a file first!",
                "msg_cancelado": "Cancel request received. Stopping...",
                "msg_cancelado_final": "Process interrupted.",
                "log_inicial": "[INFO] AutoSub v0.4 ready. Select a file...",
                "log_arquivo": "[INFO] File loaded: ",
                "log_pasta": "[INFO] Output folder set: ",
                "log_modelo_carregando": "[INFO] Loading Whisper model: ",
                "log_modelo_carregado": "[INFO] Model loaded!",
                "log_transcrevendo": "[INFO] Transcribing audio... (this may take a while)",
                "log_transcricao_concluida": "[INFO] Transcription completed! {} segments found.",
                "log_traduzindo": "[INFO] Translating to Portuguese (BR)...",
                "log_traducao_concluida": "[INFO] Translation completed! Success: {}, Failures: {}",
                "log_gerando": "[INFO] Generating subtitle file...",
                "log_sucesso": "[SUCCESS] Subtitles generated at: ",
                "log_erro": "[ERROR] An error occurred: ",
                "log_cancelado": "[CANCELLED] Process interrupted.",
                "log_aviso_traducao": "[WARNING] Failed to translate segment {}: {}"
            },
            "pt": {
                "titulo": "AutoSub",
                "subtitulo": "Gerador de Legendas Automáticas (100% Free)",
                "btn_selecionar": "📂 Selecionar Vídeo/Áudio",
                "lbl_arquivo": "Nenhum ficheiro selecionado",
                "btn_pasta": "📁 Pasta Destino",
                "lbl_pasta": "Pasta padrão (mesma do ficheiro)",
                "lbl_idioma": "🌐 Idioma do Áudio:",
                "lbl_modelo": "🧠 Modelo Whisper:",
                "lbl_formato": "📄 Formato de Saída:",
                "chk_traduzir": "Traduzir para Português (BR)",
                "btn_gerar": "▶ Gerar Legendas",
                "btn_cancelar": "⏹ Cancelar",
                "btn_abrir_pasta": "📂 Abrir Pasta de Destino",
                "status_aguardando": "Aguardando...",
                "status_carregar_modelo": "A carregar modelo...",
                "status_transcrever": "A transcrever áudio...",
                "status_traduzir": "A traduzir...",
                "status_gerar": "A gerar legendas...",
                "status_concluido": "Concluído!",
                "msg_sucesso": "Legendas geradas com sucesso!\n\nGuardado em:\n",
                "msg_erro": "Ocorreu um erro:\n",
                "msg_aviso_arquivo": "Seleciona um ficheiro primeiro!",
                "msg_cancelado": "Pedido de cancelamento recebido. A parar...",
                "msg_cancelado_final": "Processo interrompido.",
                "log_inicial": "[INFO] AutoSub v0.4 pronta. Seleciona um ficheiro...",
                "log_arquivo": "[INFO] Ficheiro carregado: ",
                "log_pasta": "[INFO] Pasta de destino definida: ",
                "log_modelo_carregando": "[INFO] A carregar modelo Whisper: ",
                "log_modelo_carregado": "[INFO] Modelo carregado!",
                "log_transcrevendo": "[INFO] A transcrever áudio... (isto pode demorar)",
                "log_transcricao_concluida": "[INFO] Transcrição concluída! {} segmentos encontrados.",
                "log_traduzindo": "[INFO] A traduzir para Português (BR)...",
                "log_traducao_concluida": "[INFO] Tradução concluída! Sucesso: {}, Falhas: {}",
                "log_gerando": "[INFO] A gerar ficheiro de legendas...",
                "log_sucesso": "[SUCESSO] Legendas geradas em: ",
                "log_erro": "[ERRO] Ocorreu um erro: ",
                "log_cancelado": "[CANCELADO] Processo interrompido.",
                "log_aviso_traducao": "[AVISO] Falha ao traduzir segmento {}: {}"
            }
        }

        # --- Frame do Topo ---
        self.frame_topo = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_topo.pack(fill="x", pady=(20, 5), padx=30)

        self.label_titulo = ctk.CTkLabel(self.frame_topo, text=self.textos[self.idioma_interface]["titulo"], font=ctk.CTkFont(size=26, weight="bold"), text_color="#00ffcc")
        self.label_titulo.pack(side="left", expand=True)

        self.btn_idioma = ctk.CTkButton(self.frame_topo, text="🇧🇷 PT", width=80, command=self.alternar_idioma, fg_color="#444444", hover_color="#555555")
        self.btn_idioma.pack(side="right")

        self.label_sub = ctk.CTkLabel(self, text=self.textos[self.idioma_interface]["subtitulo"], font=ctk.CTkFont(size=12), text_color="#aaaaaa")
        self.label_sub.pack(pady=(0, 20))

        # --- Frame de Seleção ---
        self.frame_selecao = ctk.CTkFrame(self, corner_radius=10)
        self.frame_selecao.pack(pady=10, padx=30, fill="x")

        self.frame_file = ctk.CTkFrame(self.frame_selecao, fg_color="transparent")
        self.frame_file.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_selecionar = ctk.CTkButton(self.frame_file, text=self.textos[self.idioma_interface]["btn_selecionar"], command=self.selecionar_arquivo, width=220)
        self.btn_selecionar.pack(side="left", padx=5)

        self.lbl_arquivo = ctk.CTkLabel(self.frame_file, text=self.textos[self.idioma_interface]["lbl_arquivo"], text_color="#aaaaaa")
        self.lbl_arquivo.pack(side="left", padx=10, fill="x", expand=True)

        self.frame_dest = ctk.CTkFrame(self.frame_selecao, fg_color="transparent")
        self.frame_dest.pack(fill="x", padx=10, pady=(5, 10))

        self.btn_pasta = ctk.CTkButton(self.frame_dest, text=self.textos[self.idioma_interface]["btn_pasta"], command=self.selecionar_pasta, width=220)
        self.btn_pasta.pack(side="left", padx=5)

        self.lbl_pasta = ctk.CTkLabel(self.frame_dest, text=self.textos[self.idioma_interface]["lbl_pasta"], text_color="#aaaaaa")
        self.lbl_pasta.pack(side="left", padx=10, fill="x", expand=True)

        # --- Frame de Opções ---
        self.frame_opcoes = ctk.CTkFrame(self, corner_radius=10)
        self.frame_opcoes.pack(pady=10, padx=30, fill="x")

        self.lbl_idioma = ctk.CTkLabel(self.frame_opcoes, text=self.textos[self.idioma_interface]["lbl_idioma"])
        self.lbl_idioma.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.idiomas = {
            "Auto-detect": None,
            "English": "en",
            "Portuguese": "pt",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Italian": "it",
            "Japanese": "ja"
        }

        self.combo_idioma = ctk.CTkComboBox(self.frame_opcoes, values=list(self.idiomas.keys()), width=250)
        self.combo_idioma.grid(row=0, column=1, padx=15, pady=10, sticky="w")
        self.combo_idioma.set("Auto-detect")

        self.lbl_modelo = ctk.CTkLabel(self.frame_opcoes, text=self.textos[self.idioma_interface]["lbl_modelo"])
        self.lbl_modelo.grid(row=1, column=0, padx=15, pady=10, sticky="w")

        self.modelos = {
            "Tiny (Faster, Less Accurate)": "tiny",
            "Base (Balanced)": "base",
            "Small (More Accurate, Slower)": "small"
        }

        self.combo_modelo = ctk.CTkComboBox(self.frame_opcoes, values=list(self.modelos.keys()), width=250)
        self.combo_modelo.grid(row=1, column=1, padx=15, pady=10, sticky="w")
        self.combo_modelo.set("Base (Balanced)")

        self.lbl_formato = ctk.CTkLabel(self.frame_opcoes, text=self.textos[self.idioma_interface]["lbl_formato"])
        self.lbl_formato.grid(row=2, column=0, padx=15, pady=10, sticky="w")

        self.combo_formato = ctk.CTkComboBox(self.frame_opcoes, values=["SRT (.srt)", "VTT (.vtt)"], width=250)
        self.combo_formato.grid(row=2, column=1, padx=15, pady=10, sticky="w")
        self.combo_formato.set("SRT (.srt)")

        self.var_traduzir = tk.BooleanVar()
        self.chk_traduzir = ctk.CTkCheckBox(self.frame_opcoes, text=self.textos[self.idioma_interface]["chk_traduzir"], variable=self.var_traduzir)
        self.chk_traduzir.grid(row=3, column=0, columnspan=2, padx=15, pady=10, sticky="w")

        # --- Frame de Botões de Ação ---
        self.frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acoes.pack(pady=20)

        self.btn_gerar = ctk.CTkButton(self.frame_acoes, text=self.textos[self.idioma_interface]["btn_gerar"], command=self.iniciar_thread, height=45, width=200, font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_gerar.pack(side="left", padx=10)

        self.btn_cancelar = ctk.CTkButton(self.frame_acoes, text=self.textos[self.idioma_interface]["btn_cancelar"], command=self.cancelar_processo, height=45, width=150, fg_color="#cc3333", hover_color="#ff4444", state="disabled", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_cancelar.pack(side="left", padx=10)

        # --- Barra de Progresso ---
        self.progresso = ctk.CTkProgressBar(self, width=720)
        self.progresso.pack(pady=5)
        self.progresso.set(0)

        self.lbl_status = ctk.CTkLabel(self, text=self.textos[self.idioma_interface]["status_aguardando"], text_color="#00ffcc")
        self.lbl_status.pack(pady=5)

        # --- Botão Abrir Pasta ---
        self.btn_abrir_pasta = ctk.CTkButton(self, text=self.textos[self.idioma_interface]["btn_abrir_pasta"], command=self.abrir_pasta, state="disabled", fg_color="#444444", hover_color="#555555")
        self.btn_abrir_pasta.pack(pady=(0, 10))

        # --- Log ---
        self.console = ctk.CTkTextbox(self, width=760, height=200, corner_radius=10)
        self.console.pack(pady=10, padx=30, fill="both", expand=True)
        self.console.insert("end", self.textos[self.idioma_interface]["log_inicial"] + "\n")
        self.console.configure(state="disabled")

    def alternar_idioma(self):
        if self.idioma_interface == "en":
            self.idioma_interface = "pt"
            self.btn_idioma.configure(text="🇺🇸 EN")
        else:
            self.idioma_interface = "en"
            self.btn_idioma.configure(text="🇧🇷 PT")

        t = self.textos[self.idioma_interface]
        self.label_titulo.configure(text=t["titulo"])
        self.label_sub.configure(text=t["subtitulo"])
        self.btn_selecionar.configure(text=t["btn_selecionar"])
        self.lbl_arquivo.configure(text=t["lbl_arquivo"])
        self.btn_pasta.configure(text=t["btn_pasta"])
        self.lbl_pasta.configure(text=t["lbl_pasta"])
        self.lbl_idioma.configure(text=t["lbl_idioma"])
        self.lbl_modelo.configure(text=t["lbl_modelo"])
        self.lbl_formato.configure(text=t["lbl_formato"])
        self.chk_traduzir.configure(text=t["chk_traduzir"])
        self.btn_gerar.configure(text=t["btn_gerar"])
        self.btn_cancelar.configure(text=t["btn_cancelar"])
        self.btn_abrir_pasta.configure(text=t["btn_abrir_pasta"])
        self.lbl_status.configure(text=t["status_aguardando"])

    def log(self, mensagem):
        print(mensagem)
        self.console.configure(state="normal")
        self.console.insert("end", mensagem + "\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def abrir_pasta(self):
        if self.ultimo_srt and os.path.exists(os.path.dirname(self.ultimo_srt)):
            pasta = os.path.dirname(self.ultimo_srt)
            try:
                if sys.platform == "win32":
                    os.startfile(pasta)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", pasta])
                else:
                    subprocess.Popen(["xdg-open", pasta])
            except Exception as e:
                self.log(f"{self.textos[self.idioma_interface]['log_erro']}{e}")

    def selecionar_arquivo(self):
        ficheiro = filedialog.askopenfilename(
            title="Select Video or Audio" if self.idioma_interface == "en" else "Selecionar Vídeo ou Áudio",
            filetypes=[
                ("All files", "*.*"),
                ("Videos", "*.mp4 *.mkv *.avi *.mov *.wmv"),
                ("Audios", "*.mp3 *.wav *.m4a *.flac *.ogg")
            ]
        )
        if ficheiro:
            self.caminho_arquivo = ficheiro
            nome_curto = os.path.basename(ficheiro)
            self.lbl_arquivo.configure(text=nome_curto)
            self.log(self.textos[self.idioma_interface]["log_arquivo"] + nome_curto)

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Select Output Folder" if self.idioma_interface == "en" else "Selecionar Pasta de Destino")
        if pasta:
            self.pasta_destino = pasta
            self.lbl_pasta.configure(text=pasta)
            self.log(self.textos[self.idioma_interface]["log_pasta"] + pasta)

    def cancelar_processo(self):
        self.cancelar = True
        self.log(self.textos[self.idioma_interface]["msg_cancelado"])
        self.btn_cancelar.configure(state="disabled")

    def iniciar_thread(self):
        if not self.caminho_arquivo:
            messagebox.showwarning("Warning" if self.idioma_interface == "en" else "Aviso", 
                                   self.textos[self.idioma_interface]["msg_aviso_arquivo"])
            return
        self.btn_selecionar.configure(state="disabled")
        self.btn_pasta.configure(state="disabled")
        self.combo_idioma.configure(state="disabled")
        self.combo_modelo.configure(state="disabled")
        self.combo_formato.configure(state="disabled")
        self.chk_traduzir.configure(state="disabled")
        self.btn_gerar.configure(state="disabled")
        self.btn_cancelar.configure(state="normal")
        self.btn_abrir_pasta.configure(state="disabled")
        self.cancelar = False
        threading.Thread(target=self.processar, daemon=True).start()

    def processar(self):
        t = self.textos[self.idioma_interface]
        try:
            modelo_nome = self.modelos.get(self.combo_modelo.get(), "base")
            self.log(t["log_modelo_carregando"] + modelo_nome)
            self.lbl_status.configure(text=t["status_carregar_modelo"])
            self.progresso.set(0.1)

            self.modelo_whisper = whisper.load_model(modelo_nome)
            self.log(t["log_modelo_carregado"])

            if self.cancelar:
                self.log(t["log_cancelado"])
                return

            self.log(t["log_transcrevendo"])
            self.lbl_status.configure(text=t["status_transcrever"])
            self.progresso.set(0.3)

            idioma_selecionado = self.idiomas.get(self.combo_idioma.get())
            resultado = self.modelo_whisper.transcribe(self.caminho_arquivo, language=idioma_selecionado, verbose=False)

            self.progresso.set(0.7)
            self.log(t["log_transcricao_concluida"].format(len(resultado['segments'])))

            if self.cancelar:
                self.log(t["log_cancelado"])
                return

            total_traduzidos = 0
            total_falhas = 0

            if self.var_traduzir.get():
                self.log(t["log_traduzindo"])
                self.lbl_status.configure(text=t["status_traduzir"])
                tradutor = Translator()

                for i, seg in enumerate(resultado["segments"]):
                    if self.cancelar:
                        self.log(t["log_cancelado"])
                        break
                    try:
                        resultado_trad = tradutor.translate(seg["text"], src='en', dest='pt')
                        if resultado_trad and resultado_trad.text:
                            seg["text"] = resultado_trad.text
                            total_traduzidos += 1
                        else:
                            total_falhas += 1
                    except Exception as e:
                        total_falhas += 1
                        self.log(t["log_aviso_traducao"].format(i+1, e))
                        time.sleep(0.5)

                self.progresso.set(0.9)
                self.log(t["log_traducao_concluida"].format(total_traduzidos, total_falhas))

            self.log(t["log_gerando"])
            self.lbl_status.configure(text=t["status_gerar"])

            legendas = []
            for i, seg in enumerate(resultado["segments"]):
                legendas.append(srt.Subtitle(
                    index=i + 1,
                    start=timedelta(seconds=seg["start"]),
                    end=timedelta(seconds=seg["end"]),
                    content=seg["text"].strip()
                ))

            if self.pasta_destino:
                pasta_saida = self.pasta_destino
            else:
                pasta_saida = os.path.dirname(self.caminho_arquivo)

            nome_base = os.path.splitext(os.path.basename(self.caminho_arquivo))[0]
            formato = self.combo_formato.get()

            if "VTT" in formato:
                caminho_srt = os.path.join(pasta_saida, f"{nome_base}.vtt")
                conteudo = srt.compose(legendas, reindex=True, start_index=1)
                conteudo_vtt = "WEBVTT\n\n" + conteudo.replace(",", ".")
                with open(caminho_srt, "w", encoding="utf-8") as f:
                    f.write(conteudo_vtt)
            else:
                caminho_srt = os.path.join(pasta_saida, f"{nome_base}.srt")
                with open(caminho_srt, "w", encoding="utf-8") as f:
                    f.write(srt.compose(legendas))

            self.ultimo_srt = caminho_srt
            self.progresso.set(1.0)
            self.lbl_status.configure(text=t["status_concluido"])
            self.log(f"\n{t['log_sucesso']}{caminho_srt}")
            messagebox.showinfo("Success" if self.idioma_interface == "en" else "Sucesso", 
                                f"{t['msg_sucesso']}{caminho_srt}")

        except Exception as e:
            self.log(f"{t['log_erro']}{e}")
            messagebox.showerror("Error" if self.idioma_interface == "en" else "Erro", 
                                 f"{t['msg_erro']}{e}")
        finally:
            self.btn_selecionar.configure(state="normal")
            self.btn_pasta.configure(state="normal")
            self.combo_idioma.configure(state="normal")
            self.combo_modelo.configure(state="normal")
            self.combo_formato.configure(state="normal")
            self.chk_traduzir.configure(state="normal")
            self.btn_gerar.configure(state="normal")
            self.btn_cancelar.configure(state="disabled")
            self.btn_abrir_pasta.configure(state="normal")
            self.lbl_status.configure(text=t["status_aguardando"])

def main():
    app = AutoSubApp()
    app.mainloop()

if __name__ == "__main__":
    main()