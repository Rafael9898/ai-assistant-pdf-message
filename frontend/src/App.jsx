import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  // guarda as mensagens do chat
  const [messages, setMessages] = useState([
    { role: 'ai', content: 'Olá! Sou seu assistente virtual. Como posso ajudar hoje?' }
  ])

  //guarda o texto escrito pelo utilizador
  const [input, setInput] = useState('')
  
  // controla se a ia esta a pensar
  const [isLoading, setIsLoading] = useState(false)

  // serve para fazer scroll automatico para o fim
  const fimDoChatRef = useRef(null)

  // desce o ecra sempre que ha mensagens novas
  useEffect(() => {
    fimDoChatRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  // executa quando clicamos em enviar
  const handleSend = async() => {
    if (input.trim() === '') return;

    // guarda a mensagem e limpa o input
    const textoUsuario = input;
    const novasMensagens = [...messages, { role: 'user', content: textoUsuario }];
    
    setMessages(novasMensagens);
    setInput('');

    //seta TRUE e liga o carregamento
    setIsLoading(true);

    try {
      // envia o pedido para o servidor python
      const resposta = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({mensagens: novasMensagens})
      });

      const dados = await resposta.json();

      // mostra a resposta da ia no ecra
      setMessages([...novasMensagens, { role: 'ai', content: dados.resposta }]);
      
    }
    catch (erro) {
      console.error("Erro ao contactar o Python:", erro);
      setMessages([...novasMensagens, { role: 'ai', content: 'Ocorreu um erro ao contactar o servidor Python.' }]);
    }
    finally {
      setIsLoading(false); // seta FALSE e desliga o aviso de carregamento
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

      <div className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}

          // permite enviar com o enter
          onKeyDown={(e) => e.key === 'Enter' && !isLoading && handleSend()}
          placeholder="Digite sua mensagem..."

          // bloqueia o input enquanto a ia pensa
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading}>Enviar</button>
      </div>
    </div>
  )
}

export default App