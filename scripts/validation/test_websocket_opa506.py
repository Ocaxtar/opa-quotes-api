"""
Validación de endpoints WebSocket para OPA-506.
Prueba la conectividad a todos los endpoints disponibles.
"""

import asyncio
import sys

try:
    import websockets
except ImportError:
    print("❌ websockets no instalado. Instalando...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets


async def test_endpoint(uri: str, name: str) -> bool:
    """Test WebSocket endpoint handshake."""
    try:
        # Conectar sin timeout en el constructor
        async with websockets.connect(uri) as ws:
            print(f"✅ {name}: Handshake exitoso")
            print(f"   URI: {uri}")
            
            # Esperar primer mensaje (timeout 10s)
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=10)
                print(f"   📨 Mensaje recibido: {message[:80]}...")
                return True
            except asyncio.TimeoutError:
                print(f"   ⚠️  Sin mensajes en 10s (Redis puede no estar publicando)")
                return True  # Handshake exitoso de todas formas
                
    except Exception as e:
        # Verificar si es error de handshake (403, 401, etc)
        if hasattr(e, 'status_code'):
            print(f"❌ {name}: Handshake falló con código {e.status_code}")
        else:
            print(f"❌ {name}: Error - {type(e).__name__}: {e}")
        print(f"   URI: {uri}")
        return False


async def main():
    """Test all WebSocket endpoints."""
    print("🔍 Validación de Endpoints WebSocket (OPA-506)\n")
    
    endpoints = [
        ("ws://localhost:8000/ws", "Endpoint raíz sin versión"),
        ("ws://localhost:8000/ws/quotes", "Endpoint con path sin versión"),
        ("ws://localhost:8000/v1/ws", "Endpoint raíz versionado"),
        ("ws://localhost:8000/v1/ws/quotes", "Endpoint con path versionado"),
    ]
    
    results = []
    for uri, name in endpoints:
        success = await test_endpoint(uri, name)
        results.append((name, success))
        print()  # Línea en blanco entre tests
    
    # Resumen
    print("=" * 60)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n🎯 Total: {passed}/{total} endpoints operativos")
    
    if passed == total:
        print("\n✅ OPA-506: Todos los endpoints WebSocket funcionando correctamente")
        return 0
    else:
        print(f"\n❌ OPA-506: {total - passed} endpoint(s) fallaron")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
