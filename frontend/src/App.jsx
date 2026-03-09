import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  // guarda as mensagens do chat
  const [messages, setMessages] = useState([
    { role: 'ai', content: 'Olá! Sou seu assistente virtual. Como posso ajudar hoje?' }
  ])

  //guarda o texto escrito pelo utilizador
  const [input, setInput] = useState('')
  
  // controla se a IA esta a pensar
  const [isLoading, setIsLoading] = useState(false)

  // guarda o ficheiro selecionado pelo utilizador
  const [ficheiro, setFicheiro] = useState(null)

  // referencia para o input de ficheiro escondido
  const ficheiroInputRef = useRef(null)

  // serve para fazer scroll automatico para o fim
  const fimDoChatRef = useRef(null)

  // desce o ecra sempre que ha mensagens novas
  useEffect(() => {
    fimDoChatRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  // executa quando clicamos em enviar
  const handleSend = async() => {

    // se nao tiver texto nem ficheiro ignora
    if (input.trim() === '' && !ficheiro) return;

    // guarda a mensagem e limpa o input
    const textoUsuario = input;
    const mensagemUtilizador = textoUsuario
      ? ficheiro
        ? `${textoUsuario} (ficheiro anexado: ${ficheiro.name})`
        : textoUsuario
      : `Ficheiro anexado: ${ficheiro.name}`;

    // guarda a mensagem e limpa a barra
    const novasMensagens = [...messages, { role: 'user', content: mensagemUtilizador }];
    setMessages(novasMensagens);
    setInput('');

    //seta TRUE e liga o carregamento
    setIsLoading(true);

    try {

      // junta o historico e o ficheiro no mesmo pacote (FormData)
      const formData = new FormData();
      formData.append('mensagens_json', JSON.stringify(novasMensagens));
      if (ficheiro) {
        formData.append('ficheiro', ficheiro);
      }

      // envia tudo para a api em python
      const resposta = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        body: formData
      });

      const dados = await resposta.json();

      // mostra a resposta da IA no ecra
      setMessages([...novasMensagens, { role: 'ai', content: dados.resposta }]);
      
    }
    catch (erro) {
      console.error("Erro ao contactar o Python:", erro);
      setMessages([...novasMensagens, { role: 'ai', content: 'Ocorreu um erro ao contactar o servidor Python.' }]);
    }
    finally {
      // no fim de tudo desliga o aviso e limpa o anexo
      setIsLoading(false);
      setFicheiro(null);
      if (ficheiroInputRef.current) ficheiroInputRef.current.value = '';
    }
  }

  // quando o utilizador escolhe um ficheiro
  const handleFicheiroChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // confirma se e excel ou csv
      const extensao = file.name.split('.').pop().toLowerCase();
      if (extensao === 'xlsx' || extensao === 'csv') {
        setFicheiro(file);
      } else {
        alert('Apenas ficheiros .xlsx e .csv são aceites!');
        e.target.value = '';
      }
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>AI Assistant</h1>
      </header>

      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content}
            </div>
          </div>
        ))}
        
        {/* mostra mensagem de loading enquanto a ia pensa */}
        {isLoading && (
          <div className="message ai">
            <div className="message-content loading-text">
              A consultar os sistemas...
            </div>
          </div>
        )}
        <div ref={fimDoChatRef} />
      </div>

      {/* mostra o nome do ficheiro anexado em cima da barra */}
      {ficheiro && (
        <div className="ficheiro-info">
          <span>{ficheiro.name}</span>
          <button onClick={() => { setFicheiro(null); if (ficheiroInputRef.current) ficheiroInputRef.current.value = ''; }} title="Remover anexo">✕</button>
        </div>
      )}

      <div className="chat-input-area">
        {/* input de ficheiro escondido */}
        <input
          type="file"
          ref={ficheiroInputRef}
          onChange={handleFicheiroChange}
          accept=".xlsx,.csv"
          style={{ display: 'none' }}
        />

        {/* area que junta o clipe de anexo e a barra de texto */}
        <div className="input-wrapper">
          <button
            className="clip-button"
            onClick={() => ficheiroInputRef.current?.click()}
            disabled={isLoading}
            title="Anexar ficheiro (.xlsx ou .csv)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="clip-icon">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
            </svg>
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isLoading && handleSend()}
            placeholder="Digite a sua mensagem..."
            disabled={isLoading}
          />
        </div>

        {/* botao de enviar */}
        <button className="send-button" onClick={handleSend} disabled={isLoading}>Enviar</button>
      </div>
    </div>
  )
}

export default App