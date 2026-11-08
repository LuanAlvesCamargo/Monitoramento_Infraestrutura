import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const blank = { numero: '', titulo: '', tipo: 'Contrato', descricao: '', status: 'Em revisao', tags: '' }
const types = ['Contrato', 'Peticao', 'Parecer', 'Termo', 'Notificacao']
const statuses = ['Ativo', 'Em revisao', 'Arquivado']
const statusLabel = (status) => status === 'Em revisao' ? 'Em revisão' : status
const tone = (status) => status === 'Ativo' ? 'active' : status === 'Arquivado' ? 'archived' : 'review'

function App() {
  const [documents, setDocuments] = useState([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState({ q: '', tipo: '', status: '' })
  const [draft, setDraft] = useState(filters)
  const [form, setForm] = useState(blank)
  const [editing, setEditing] = useState(null)
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [cache, setCache] = useState('—')
  const query = useMemo(() => new URLSearchParams(Object.entries(filters).filter(([, value]) => value)).toString(), [filters])
  const counts = useMemo(() => ({
    ativos: documents.filter((document) => document.status === 'Ativo').length,
    revisao: documents.filter((document) => document.status === 'Em revisao').length,
    arquivados: documents.filter((document) => document.status === 'Arquivado').length,
  }), [documents])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`/api/documentos?limite=100${query ? `&${query}` : ''}`)
      const body = await response.json()
      if (!response.ok) throw new Error(body.erro || 'Falha ao carregar documentos.')
      setDocuments(body.itens)
      setTotal(body.paginacao.total)
      setCache(response.headers.get('X-Cache') || 'BYPASS')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [query])
  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value })
  function begin(item) {
    setEditing(item || null)
    setForm(item ? { ...item, tags: item.tags.join(', ') } : blank)
    setOpen(true)
  }
  async function save(event) {
    event.preventDefault()
    setError('')
    const body = { ...form, tags: form.tags.split(',').map((tag) => tag.trim()).filter(Boolean) }
    try {
      const response = await fetch(editing ? `/api/documentos/${editing.id}` : '/api/documentos', {
        method: editing ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.erro || 'Não foi possível salvar.')
      setOpen(false)
      setNotice(editing ? 'Documento atualizado.' : 'Documento cadastrado.')
      await load()
    } catch (err) { setError(err.message) }
  }
  async function remove(item) {
    if (!window.confirm(`Excluir ${item.numero}?`)) return
    try {
      const response = await fetch(`/api/documentos/${item.id}`, { method: 'DELETE' })
      if (!response.ok) throw new Error('Não foi possível excluir.')
      setNotice('Documento excluído.')
      await load()
    } catch (err) { setError(err.message) }
  }
  function clearFilters() {
    const next = { q: '', tipo: '', status: '' }
    setDraft(next)
    setFilters(next)
  }

  return <div className="app-shell">
    <header className="service-bar">
      <div className="service-name"><span className="mark" aria-hidden="true">JD</span><strong>JurisDocs</strong><span>Catálogo documental</span></div>
      <div className="service-meta"><span>Ambiente acadêmico</span><span className={`cache-state ${cache.toLowerCase()}`}>Cache: {cache}</span></div>
    </header>
    <div className="app-body">
      <aside className="side-nav" aria-label="Navegação principal">
        <div className="nav-section">
          <p>Consulta</p>
          <a className="nav-item current" href="#documentos" aria-current="page"><span className="nav-glyph">▤</span>Documentos</a>
          <a className="nav-item" href="#filtros"><span className="nav-glyph">⌕</span>Pesquisa avançada</a>
        </div>
        <div className="nav-section">
          <p>Cadastro</p>
          <button className="nav-item" onClick={() => begin()}><span className="nav-glyph">＋</span>Novo documento</button>
        </div>
        <div className="nav-foot">MongoDB e Redis<br />execução local</div>
      </aside>
      <main className="content">
        <div className="page-heading">
          <div><p className="breadcrumb">Consulta documental / Acervo principal</p><h1>Documentos cadastrados</h1><p className="intro">Pesquise, filtre e mantenha os registros acadêmicos utilizados na demonstração do MongoDB e Redis.</p></div>
          <button className="primary" onClick={() => begin()}>Cadastrar documento</button>
        </div>
        <section className="summary" aria-label="Resumo da consulta">
          <div><span>Resultados</span><strong>{total}</strong><small>registro(s) na consulta</small></div>
          <div><span>Ativos</span><strong>{counts.ativos}</strong><small>disponíveis para uso</small></div>
          <div><span>Em revisão</span><strong>{counts.revisao}</strong><small>aguardando validação</small></div>
          <div><span>Arquivados</span><strong>{counts.arquivados}</strong><small>consulta histórica</small></div>
        </section>
        <section className="query-panel" id="filtros">
          <div className="panel-title"><div><h2>Localizar documento</h2><p>Informe um termo ou restrinja os resultados pelos campos de classificação.</p></div><button className="refresh" onClick={load} disabled={loading}>Atualizar lista</button></div>
          <form className="filters" onSubmit={(event) => { event.preventDefault(); setFilters(draft) }}>
            <label className="wide">Termo de busca<input aria-label="Buscar documentos" placeholder="Número, título, descrição ou tag" value={draft.q} onChange={(event) => setDraft({ ...draft, q: event.target.value })}/></label>
            <label>Tipo<select value={draft.tipo} onChange={(event) => setDraft({ ...draft, tipo: event.target.value })}><option value="">Todos</option>{types.map((type) => <option key={type}>{type}</option>)}</select></label>
            <label>Status<select value={draft.status} onChange={(event) => setDraft({ ...draft, status: event.target.value })}><option value="">Todos</option>{statuses.map((status) => <option key={status} value={status}>{statusLabel(status)}</option>)}</select></label>
            <div className="filter-actions"><button className="primary">Pesquisar</button><button type="button" className="plain" onClick={clearFilters}>Limpar campos</button></div>
          </form>
        </section>
        {error && <div className="message error" role="alert">{error}</div>}
        {notice && <div className="message ok" role="status">{notice}</div>}
        <section className="results" id="documentos">
          <div className="result-title"><div><h2>Resultado da consulta</h2><p>{loading ? 'Atualizando os registros...' : `${total} registro(s) encontrado(s)`}</p></div><span className="source-note">Fonte: API Flask / MongoDB</span></div>
          <div className="table-scroll"><table><thead><tr><th>Número</th><th>Documento</th><th>Classificação</th><th>Status</th><th>Atualizado em</th><th><span className="sr-only">Ações</span></th></tr></thead>
            <tbody>{!loading && documents.map((item) => <tr key={item.id}><td className="doc-number">{item.numero}</td><td><strong>{item.titulo}</strong><p>{item.descricao}</p>{item.tags.length > 0 && <div className="tag-list">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>}</td><td>{item.tipo}</td><td><span className={`status ${tone(item.status)}`}>{statusLabel(item.status)}</span></td><td>{new Date(item.dataAtualizacao).toLocaleDateString('pt-BR')}</td><td className="row-actions"><button onClick={() => begin(item)}>Editar</button><button className="delete" onClick={() => remove(item)}>Excluir</button></td></tr>)}</tbody>
          </table></div>
          {!loading && !documents.length && <div className="empty">Nenhum documento corresponde aos filtros informados.</div>}
        </section>
      </main>
    </div>
    {open && <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="document-form-title"><form className="drawer" onSubmit={save}>
      <div className="drawer-head"><div><p className="breadcrumb">{editing ? 'Alteração de registro' : 'Novo registro'}</p><h2 id="document-form-title">{editing ? editing.numero : 'Cadastrar documento'}</h2></div><button type="button" className="close" aria-label="Fechar formulário" onClick={() => setOpen(false)}>×</button></div>
      <p className="form-intro">Os dados serão persistidos no MongoDB. As consultas posteriores usam a estratégia cache-aside do Redis.</p>
      <label>Número do documento<input required disabled={Boolean(editing)} name="numero" value={form.numero} onChange={update}/></label>
      <label>Título<input required name="titulo" value={form.titulo} onChange={update}/></label>
      <div className="form-grid"><label>Tipo<select name="tipo" value={form.tipo} onChange={update}>{types.map((type) => <option key={type}>{type}</option>)}</select></label><label>Status<select name="status" value={form.status} onChange={update}>{statuses.map((status) => <option key={status} value={status}>{statusLabel(status)}</option>)}</select></label></div>
      <label>Descrição<textarea required name="descricao" value={form.descricao} onChange={update} rows="5"/></label>
      <label>Tags <small>separadas por vírgula</small><input name="tags" value={form.tags} onChange={update}/></label>
      <div className="drawer-actions"><button type="button" className="plain" onClick={() => setOpen(false)}>Cancelar</button><button className="primary">Salvar documento</button></div>
    </form></div>}
  </div>
}

createRoot(document.getElementById('root')).render(<App />)
