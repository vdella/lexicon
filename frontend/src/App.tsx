import React, { useState } from 'react'
import Plot from 'react-plotly.js'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export default function App() {
    const [regex, setRegex] = useState('(a|b)*abb')
    const [activePage, setActivePage] = useState(0)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)

    async function analyze() {
        setError(null)
        const res = await fetch(`${API_BASE}/api/v1/regex/analyze`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ regex, active_page: activePage })
        })
        const data = await res.json()
        if (!res.ok) {
            setError(data?.detail || 'Request failed')
            setResult(null)
            return
        }
        setResult(data)
    }

    const fig = result?.figure
    const pageQty = result?.page_quantity ?? 0

    return (
        <div style={{maxWidth: 1100, margin: '0 auto', padding: 24, fontFamily: 'system-ui, sans-serif'}}>
            <h1 style={{textAlign:'center'}}>Rosetta (React + FastAPI)</h1>

            <div style={{display:'flex', gap: 12, justifyContent:'center', alignItems:'center', flexWrap:'wrap'}}>
                <input
                    value={regex}
                    onChange={e => setRegex(e.target.value)}
                    placeholder="Type your regex (e.g. (a|b)*abb)"
                    style={{width: 420, padding: 10, fontSize: 14}}
                />
                <input
                    type="number"
                    value={activePage}
                    min={0}
                    max={Math.max(pageQty-1, 0)}
                    onChange={e => setActivePage(Number(e.target.value))}
                    style={{width: 120, padding: 10}}
                    title="0 hides metadata; >0 reveals progressively"
                />
                <button onClick={analyze} style={{padding:'10px 16px'}}>Submit</button>
            </div>

            {error && (
                <div style={{marginTop: 16, padding: 12, border: '1px solid #c00', color: '#c00'}}>
                    {error}
                </div>
            )}

            {result && (
                <>
                    <div style={{marginTop: 18, border: '1px solid #ddd', borderRadius: 8, padding: 8}}>
                        <Plot
                            data={fig.data}
                            layout={fig.layout}
                            style={{width: '100%', height: 520}}
                            useResizeHandler
                            config={{displayModeBar: true}}
                        />
                    </div>

                    <div style={{marginTop: 18, display:'grid', gridTemplateColumns:'1fr 1fr', gap: 12}}>
                        <div style={{border: '1px solid #ddd', borderRadius: 8, padding: 12}}>
                            <h3>follow_pos table</h3>
                            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(result.follow_pos_table, null, 2)}</pre>
                        </div>

                        <div style={{border: '1px solid #ddd', borderRadius: 8, padding: 12}}>
                            <h3>FA transitions</h3>
                            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(result.fa_table, null, 2)}</pre>
                        </div>
                    </div>

                    <div style={{marginTop: 18, border: '1px solid #ddd', borderRadius: 8, padding: 12}}>
                        <h3>FA diagram</h3>
                        {result.fa_png ? (
                            <img alt="fa diagram" src={result.fa_png} style={{maxWidth:'100%'}} />
                        ) : (
                            <pre style={{whiteSpace:'pre-wrap'}}>{result.fa_dot}</pre>
                        )}
                    </div>
                </>
            )}
        </div>
    )
}
