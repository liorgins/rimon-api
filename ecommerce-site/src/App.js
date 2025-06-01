import './App.css';
import React, { useEffect, useState, useRef } from 'react';
import config from './config';
import { GoogleOAuthProvider, GoogleLogin, googleLogout } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';

function sanitize(str) {
  if (!str) return '';
  return str
    .toString()
    .trim()
    .replace(/^"+|"+$/g, '') // Remove leading/trailing double quotes
    .replace(/\s+/g, ' ')     // Collapse multiple spaces
    .toLowerCase();
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

console.log('App loaded: waiting for Google signup/login...');

function App() {
  const [products, setProducts] = useState([]);
  const [heDict, setHeDict] = useState({});
  const [categories, setCategories] = useState([]);
  const [catDict, setCatDict] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [cart, setCart] = useState([]);
  const [showCart, setShowCart] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const THRESHOLD = config.SEARCH_THRESHOLD;
  let missingHebrewKeys = [];
  const [user, setUser] = useState(null);
  const [showAvatarMenu, setShowAvatarMenu] = useState(false);
  const avatarMenuRef = useRef();

  useEffect(() => {
    Promise.all([
      fetch(process.env.PUBLIC_URL + '/products.json').then((res) => res.json()),
      fetch(process.env.PUBLIC_URL + '/products_dictionary.json').then((res) => res.json()),
      fetch(process.env.PUBLIC_URL + '/categories.json').then((res) => res.json()),
      fetch(process.env.PUBLIC_URL + '/categories_dictionary.json').then((res) => res.json()),
    ])
      .then(([productsData, dictJson, categoriesData, catDictJson]) => {
        setProducts(productsData);
        setHeDict(dictJson);
        setCategories(categoriesData);
        setCatDict(catDictJson);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Poll update.json every 10 seconds and reload if changed
  useEffect(() => {
    let prevUpdate = null;
    const interval = setInterval(() => {
      fetch(process.env.PUBLIC_URL + '/update.json', { cache: 'no-store' })
        .then(res => res.json())
        .then(data => {
          if (prevUpdate && data.updated !== prevUpdate) {
            window.location.reload();
          }
          prevUpdate = data.updated;
          setLastUpdate(data.updated);
        })
        .catch(() => {});
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const scoredProducts = products.map((product) => {
    if (!search) return { product, score: 1 };
    const dictEntry = heDict[`${sanitize(product.id)},${sanitize(product.sku)}`] || {};
    const hebrew = sanitize(dictEntry.hebrew);
    const english = sanitize(dictEntry.english);
    const title = sanitize(product.title);
    const s = sanitize(search);
    const scores = [
      fuzzyScore(hebrew, s),
      fuzzyScore(english, s),
      fuzzyScore(title, s),
    ];
    return { product, score: Math.max(...scores) };
  });

  let filteredProducts = scoredProducts
    .filter(({ score }) => score >= THRESHOLD)
    .sort((a, b) => b.score - a.score)
    .map(({ product }) => product);

  if (selectedCategory) {
    filteredProducts = filteredProducts.filter((product) => {
      // categoriesIds is a string like ",2554,2556,"
      return product.categoriesIds && product.categoriesIds.includes(`,${selectedCategory},`);
    });
  }

  function addToCart(product) {
    setCart((prev) => {
      const existing = prev.find((item) => item.id === product.id);
      if (existing) {
        return prev.map((item) =>
          item.id === product.id ? { ...item, qty: item.qty + 1 } : item
        );
      } else {
        return [...prev, { ...product, qty: 1 }];
      }
    });
  }

  function removeFromCart(productId) {
    setCart((prev) => prev.filter((item) => item.id !== productId));
  }

  function changeQty(productId, delta) {
    setCart((prev) =>
      prev
        .map((item) =>
          item.id === productId ? { ...item, qty: Math.max(1, item.qty + delta) } : item
        )
        .filter((item) => item.qty > 0)
    );
  }

  const cartCount = cart.reduce((sum, item) => sum + item.qty, 0);
  const cartTotal = cart.reduce((sum, item) => sum + item.qty * item.finalPrice, 0);

  useEffect(() => {
    if (missingHebrewKeys.length > 0) {
      console.debug('Missing Hebrew keys:', missingHebrewKeys);
      console.debug('Total missing:', missingHebrewKeys.length);
    }
  }, [products, heDict, filteredProducts]);

  // Google login success handler
  const handleGoogleLogin = (credentialResponse) => {
    if (credentialResponse.credential) {
      const decoded = jwtDecode(credentialResponse.credential);
      setUser(decoded);
      localStorage.setItem('user', JSON.stringify(decoded));
      console.log('Google login success:', decoded);
    } else {
      console.error('Google login: No credential received');
    }
  };

  // Google logout
  const handleLogout = () => {
    console.log('Logout: start');
    setUser(null);
    console.log('Logout: setUser(null)');
    localStorage.removeItem('user');
    console.log('Logout: localStorage.removeItem');
    googleLogout();
    console.log('Logout: googleLogout() called');
    setCart([]);
    console.log('Logout: setCart([])');
    setTimeout(() => {
      console.log('Logout: reloading page');
      window.location.reload();
    }, 100);
  };

  useEffect(() => {
    // Restore user from localStorage
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      console.log('User restored from localStorage:', JSON.parse(savedUser));
    }
  }, []);

  useEffect(() => {
    // Load cart from localStorage per user
    let key = user ? `cart_${user.sub || user.email}` : 'cart_guest';
    const savedCart = localStorage.getItem(key);
    if (savedCart) {
      setCart(JSON.parse(savedCart));
    } else {
      setCart([]);
    }
  }, [user]);

  useEffect(() => {
    // Save cart to localStorage per user
    let key = user ? `cart_${user.sub || user.email}` : 'cart_guest';
    localStorage.setItem(key, JSON.stringify(cart));
  }, [cart, user]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (avatarMenuRef.current && !avatarMenuRef.current.contains(e.target)) {
        setShowAvatarMenu(false);
      }
    }
    if (showAvatarMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showAvatarMenu]);

  // --- LOGGING FOR DEBUGGING ---
  useEffect(() => {
    console.log('User state changed:', user);
  }, [user]);
  useEffect(() => {
    console.log('Cart state changed:', cart);
  }, [cart]);

  // --- AVATAR LOGGING ---
  useEffect(() => {
    if (user) {
      if (user.picture && user.picture.trim()) {
        console.log('Trying to render avatar image:', user.picture);
      } else {
        console.log('Rendering fallback avatar icon (no image)');
      }
    }
  }, [user]);

  return (
    <GoogleOAuthProvider clientId="424276917259-055s59en5rcplijem54e3sl5i347u0qs.apps.googleusercontent.com">
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
          <select
            value={selectedCategory}
            onChange={e => setSelectedCategory(e.target.value)}
            style={{ fontSize: '1.1rem', padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid #ccc', minWidth: 180 }}
          >
            <option value="">כל הקטגוריות</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>
                {catDict[sanitize(cat.category_name)] || cat.category_name}
              </option>
            ))}
          </select>
          <button onClick={() => setShowCart(true)} style={{ position: 'relative', background: 'none', border: 'none', cursor: 'pointer', marginRight: 16 }}>
            <span role="img" aria-label="cart" style={{ fontSize: '2rem' }}>🛒</span>
            {cartCount > 0 && (
              <span style={{ position: 'absolute', top: 0, right: 0, background: '#7b1fa2', color: '#fff', borderRadius: '50%', width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '1rem' }}>{cartCount}</span>
            )}
          </button>
        </div>
        <h2 style={{ color: '#333', margin: '2rem 2rem 0 0' }}>כל המוצרים</h2>
        {loading && <p style={{ margin: '2rem' }}>טוען מוצרים...</p>}
        {error && <p style={{ color: 'red', margin: '2rem' }}>שגיאה: {error}</p>}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '2rem', margin: '2rem' }}>
          {filteredProducts.map((product) => {
            const dictEntry = heDict[`${sanitize(product.id)},${sanitize(product.sku)}`] || {};
            const hebrewName = dictEntry.hebrew || product.title;
            if (!dictEntry.hebrew) {
              missingHebrewKeys.push(`${sanitize(product.id)},${sanitize(product.sku)}`);
            }
            return (
              <div key={product.id} style={{ background: '#fff', borderRadius: '12px', boxShadow: '0 2px 8px #0001', padding: '1rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <img src={product.imgSrc} alt={hebrewName} style={{ width: '120px', height: '120px', objectFit: 'contain', marginBottom: '1rem', borderRadius: '8px', background: '#eee' }} />
                <div style={{ fontWeight: 'bold', fontSize: '1.1rem', marginBottom: '0.5rem', textAlign: 'center' }}>{hebrewName}</div>
                <div style={{ color: '#7b1fa2', fontWeight: 'bold', marginBottom: '0.5rem' }}>{product.finalPrice} {product.currency}</div>
                <div style={{ color: '#666', fontSize: '0.9rem', marginBottom: '0.5rem', textAlign: 'center' }}>{product.categories}</div>
                {product.available ? (
                  <button style={{ background: '#7b1fa2', color: '#fff', border: 'none', borderRadius: '6px', padding: '0.5rem 1.2rem', cursor: 'pointer', marginTop: 'auto' }} onClick={() => addToCart(product)}>הוסף לסל</button>
                ) : (
                  <div style={{ color: 'red', fontWeight: 'bold' }}>אזל מהמלאי</div>
                )}
              </div>
            );
          })}
        </div>
        {showCart && (
          <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: '#0008', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => setShowCart(false)}>
            <div style={{ background: '#fff', borderRadius: 16, minWidth: 340, maxWidth: 480, padding: 24, boxShadow: '0 4px 24px #0003', position: 'relative' }} onClick={e => e.stopPropagation()}>
              <button onClick={() => setShowCart(false)} style={{ position: 'absolute', left: 16, top: 16, background: 'none', border: 'none', fontSize: 24, cursor: 'pointer' }}>✖️</button>
              <h2 style={{ marginTop: 0, color: '#7b1fa2' }}>סל קניות</h2>
              {cart.length === 0 ? (
                <p>הסל ריק</p>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 16 }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #ccc' }}>
                      <th style={{ textAlign: 'right', padding: 8 }}>מוצר</th>
                      <th style={{ textAlign: 'center', padding: 8 }}>כמות</th>
                      <th style={{ textAlign: 'center', padding: 8 }}>מחיר</th>
                      <th style={{ textAlign: 'center', padding: 8 }}>סה"כ</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {cart.map(item => {
                      const dictEntry = heDict[`${sanitize(item.id)},${sanitize(item.sku)}`] || {};
                      const hebrewName = dictEntry.hebrew || item.title;
                      return (
                        <tr key={item.id}>
                          <td style={{ textAlign: 'right', padding: 8 }}>{hebrewName}</td>
                          <td style={{ textAlign: 'center', padding: 8 }}>
                            <button onClick={() => changeQty(item.id, -1)} style={{ margin: '0 4px', border: '1px solid #ccc', borderRadius: 4, background: '#eee', width: 24, height: 24, fontWeight: 'bold', cursor: 'pointer' }}>-</button>
                            {item.qty}
                            <button onClick={() => changeQty(item.id, 1)} style={{ margin: '0 4px', border: '1px solid #ccc', borderRadius: 4, background: '#eee', width: 24, height: 24, fontWeight: 'bold', cursor: 'pointer' }}>+</button>
                          </td>
                          <td style={{ textAlign: 'center', padding: 8 }}>{item.finalPrice} {item.currency}</td>
                          <td style={{ textAlign: 'center', padding: 8 }}>{(item.finalPrice * item.qty).toFixed(2)} {item.currency}</td>
                          <td style={{ textAlign: 'center', padding: 8 }}>
                            <button onClick={() => removeFromCart(item.id)} style={{ background: 'none', border: 'none', color: 'red', fontWeight: 'bold', cursor: 'pointer' }}>הסר</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
              <div style={{ textAlign: 'left', fontWeight: 'bold', fontSize: '1.2rem', color: '#7b1fa2' }}>
                סה"כ: {cartTotal.toFixed(2)} {cart[0]?.currency || ''}
              </div>
            </div>
          </div>
        )}
        <div style={{ position: 'fixed', top: 60, left: 24, zIndex: 300, minWidth: 60 }}>
          {user ? (
            <div style={{ position: 'relative' }} ref={avatarMenuRef}>
              {(user.picture && user.picture.trim()) ? (
                <img
                  src={user.picture}
                  alt="avatar"
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    border: '2px solid #7b1fa2',
                    cursor: 'pointer',
                    background: '#fff',
                    overflow: 'hidden',
                    padding: 0,
                    objectFit: 'cover',
                  }}
                  onClick={() => { console.log('Avatar image clicked'); setShowAvatarMenu(v => !v); }}
                  onLoad={() => console.log('Avatar image loaded successfully:', user.picture)}
                  onError={() => console.log('Avatar image failed to load:', user.picture)}
                />
              ) : (
                <div
                  onClick={() => { console.log('Avatar fallback clicked'); setShowAvatarMenu(v => !v); }}
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    border: '2px solid #7b1fa2',
                    background: '#e1d7ee',
                    color: '#7b1fa2',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 'bold',
                    fontSize: 28,
                    cursor: 'pointer',
                    userSelect: 'none',
                    boxShadow: '0 2px 8px #0001',
                    overflow: 'hidden',
                    padding: 0,
                  }}
                >
                  <span role="img" aria-label="user">👤</span>
                </div>
              )}
              {showAvatarMenu && (
                <div
                  style={{
                    position: 'absolute',
                    top: 50,
                    left: 0,
                    background: '#fff',
                    boxShadow: '0 2px 12px #0002',
                    borderRadius: 12,
                    padding: '14px 18px 10px 18px',
                    minWidth: 120,
                    zIndex: 1000,
                    textAlign: 'center',
                  }}
                >
                  <div style={{ marginBottom: 8, color: '#7b1fa2', fontWeight: 'bold', fontSize: '1.1rem' }}>
                    {user.name ? `שלום, ${user.name.split(' ')[0]}` : 'שלום!'}
                  </div>
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      console.log('Logout button clicked');
                      setShowAvatarMenu(false);
                      handleLogout();
                    }}
                    style={{ background: '#eee', color: '#7b1fa2', border: 'none', borderRadius: 8, padding: '8px 16px', cursor: 'pointer', fontWeight: 'bold', width: '100%' }}
                  >
                    התנתק
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <GoogleLogin
                onSuccess={handleGoogleLogin}
                onError={() => { console.error('Google Login Failed'); alert('Google Login Failed'); }}
                useOneTap
                text="signin_with"
                width="180"
                size="medium"
                shape="pill"
                theme="outline"
                locale="he"
                ux_mode="popup"
              />
              <GoogleLogin
                onSuccess={handleGoogleLogin}
                onError={() => { console.error('Google Signup Failed'); alert('Google Signup Failed'); }}
                text="signup_with"
                width="180"
                size="medium"
                shape="pill"
                theme="filled_blue"
                locale="he"
                ux_mode="popup"
                prompt="consent"
              />
              <div style={{ fontSize: '0.9rem', color: '#666', marginTop: 2 }}>או הירשם עם גוגל</div>
            </div>
          )}
        </div>
      </div>
    </GoogleOAuthProvider>
  );
}

export default App;
