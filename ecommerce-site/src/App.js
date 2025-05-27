import './App.css';
import React, { useEffect, useState } from 'react';
import config from './config';

function csvToDict(csv) {
  const lines = csv.split('\n');
  const dict = {};
  for (let i = 1; i < lines.length; i++) {
    const row = lines[i].split(',');
    if (row.length < 4) continue;
    const id = row[0].trim();
    const hebrew = row[3].replace(/^"|"$/g, '').trim();
    const english = row[2].replace(/^"|"$/g, '').trim();
    if (id) dict[id] = { hebrew, english };
  }
  return dict;
}

// Fuzzy scoring: 1 = exact, 0.8 = includes, 0.5 = fuzzy, 0 = no match
function fuzzyScore(str, query) {
  if (!str || !query) return 0;
  str = str.toLowerCase();
  query = query.toLowerCase();
  if (str === query) return 1;
  if (str.includes(query)) return 0.8;
  // Fuzzy: all query chars appear in order in str
  let i = 0;
  for (let c of str) {
    if (c === query[i]) i++;
    if (i === query.length) return 0.5;
  }
  return 0;
}

function App() {
  const [products, setProducts] = useState([]);
  const [heDict, setHeDict] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const THRESHOLD = config.SEARCH_THRESHOLD;

  useEffect(() => {
    Promise.all([
      fetch(process.env.PUBLIC_URL + '/products.json').then((res) => res.json()),
      fetch(process.env.PUBLIC_URL + '/products_dictionary.csv').then((res) => res.text()),
    ])
      .then(([productsData, dictCsv]) => {
        setProducts(productsData);
        setHeDict(csvToDict(dictCsv));
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const scoredProducts = products.map((product) => {
    if (!search) return { product, score: 1 };
    const dictEntry = heDict[product.id?.toString()] || {};
    const hebrew = dictEntry.hebrew || '';
    const english = dictEntry.english || '';
    const title = product.title || '';
    const scores = [
      fuzzyScore(hebrew, search),
      fuzzyScore(english, search),
      fuzzyScore(title, search),
    ];
    return { product, score: Math.max(...scores) };
  });

  const filteredProducts = scoredProducts
    .filter(({ score }) => score >= THRESHOLD)
    .sort((a, b) => b.score - a.score)
    .map(({ product }) => product);

  return (
    <div className="App" style={{ direction: 'rtl', textAlign: 'right', fontFamily: 'Heebo, Arial, sans-serif', background: '#f5f5f5', minHeight: '100vh' }}>
      <div style={{ position: 'sticky', top: 0, background: '#fff', zIndex: 100, padding: '1rem 2rem', boxShadow: '0 2px 8px #0001', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <h1 style={{ color: '#7b1fa2', margin: 0, fontSize: '2rem', flex: 'none' }}>חנות רימון</h1>
        <input
          type="text"
          placeholder="חפש מוצר בעברית או באנגלית..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ flex: 1, fontSize: '1.1rem', padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid #ccc', direction: 'rtl' }}
        />
      </div>
      <h2 style={{ color: '#333', margin: '2rem 2rem 0 0' }}>כל המוצרים</h2>
      {loading && <p style={{ margin: '2rem' }}>טוען מוצרים...</p>}
      {error && <p style={{ color: 'red', margin: '2rem' }}>שגיאה: {error}</p>}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '2rem', margin: '2rem' }}>
        {filteredProducts.map((product) => {
          const dictEntry = heDict[product.id?.toString()] || {};
          const hebrewName = dictEntry.hebrew || product.title;
          return (
            <div key={product.id} style={{ background: '#fff', borderRadius: '12px', boxShadow: '0 2px 8px #0001', padding: '1rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <img src={product.imgSrc} alt={hebrewName} style={{ width: '120px', height: '120px', objectFit: 'contain', marginBottom: '1rem', borderRadius: '8px', background: '#eee' }} />
              <div style={{ fontWeight: 'bold', fontSize: '1.1rem', marginBottom: '0.5rem', textAlign: 'center' }}>{hebrewName}</div>
              <div style={{ color: '#7b1fa2', fontWeight: 'bold', marginBottom: '0.5rem' }}>{product.finalPrice} {product.currency}</div>
              <div style={{ color: '#666', fontSize: '0.9rem', marginBottom: '0.5rem', textAlign: 'center' }}>{product.categories}</div>
              {product.available ? (
                <button style={{ background: '#7b1fa2', color: '#fff', border: 'none', borderRadius: '6px', padding: '0.5rem 1.2rem', cursor: 'pointer', marginTop: 'auto' }}>הוסף לסל</button>
              ) : (
                <div style={{ color: 'red', fontWeight: 'bold' }}>אזל מהמלאי</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default App;
