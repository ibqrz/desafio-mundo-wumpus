import random
from collections import deque

class MundoWumpus:
    def __init__(self, pos_robo, pos_ouro, pos_wumpus, pocos):
        self.tamanho = 4
        self.pos_robo = pos_robo
        self.pos_ouro = pos_ouro
        self.pos_wumpus = pos_wumpus
        self.pocos = pocos

        # Matriz de Conhecimento:
        # '?'  = Desconhecido
        # 'OK' = Seguro
        # '?W' = Possível Wumpus
        # '?P' = Possível Poço
        # 'W'  = Wumpus Confirmado
        # 'P'  = Poço Confirmado
        self.conhecimento = [['?' for _ in range(4)] for _ in range(4)]
        self.visitadas = set()
        
        # Histórico de leituras por posição: (x, y) -> {'fedor': bool, 'brisa': bool}
        self.historico_leituras = {}

        # A posição inicial é 100% segura
        self.conhecimento[pos_robo[1]][pos_robo[0]] = 'OK'

    def eh_valida(self, x, y):
        return 0 <= x < 4 and 0 <= y < 4

    def get_vizinhos(self, x, y):
        vizs = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.eh_valida(nx, ny):
                vizs.append((nx, ny))
        return vizs

    def ler_sensores(self, x, y):
        fedor = any(v == self.pos_wumpus for v in self.get_vizinhos(x, y))
        brisa = any(v in self.pocos for v in self.get_vizinhos(x, y))
        brilho = (x, y) == self.pos_ouro
        return fedor, brisa, brilho

    def inferir_logica(self):
        mudou = True
        while mudou:
            mudou = False

            # 1. Salas visitadas são sempre 'OK'
            for (lx, ly) in self.historico_leituras.keys():
                if self.conhecimento[ly][lx] != 'OK':
                    self.conhecimento[ly][lx] = 'OK'
                    mudou = True

            # Check: Já temos um Wumpus confirmado no mapa?
            wumpus_encontrado = any(
                self.conhecimento[y][x] == 'W' 
                for y in range(4) for x in range(4)
            )

            # 2. Análise de cada célula para eliminar riscos ou registrar suspeitas
            for y in range(4):
                for x in range(4):
                    if self.conhecimento[y][x] in ['OK', 'W', 'P']:
                        continue

                    pode_ser_wumpus = not wumpus_encontrado
                    pode_ser_poco = True

                    for (lx, ly), s in self.historico_leituras.items():
                        if (x, y) in self.get_vizinhos(lx, ly):
                            if not s['fedor']:
                                pode_ser_wumpus = False
                            if not s['brisa']:
                                pode_ser_poco = False

                    # Se não pode ser Wumpus nem Poço -> Torna-se SEGURA
                    if not pode_ser_wumpus and not pode_ser_poco:
                        if self.conhecimento[y][x] != 'OK':
                            self.conhecimento[y][x] = 'OK'
                            mudou = True
                    elif pode_ser_wumpus and not pode_ser_poco:
                        if self.conhecimento[y][x] != '?W':
                            self.conhecimento[y][x] = '?W'
                            mudou = True
                    elif pode_ser_poco and not pode_ser_wumpus:
                        if self.conhecimento[y][x] != '?P':
                            self.conhecimento[y][x] = '?P'
                            mudou = True

            # 3. Dedução de Certeza do Wumpus por Unicidade / Interseção
            if not wumpus_encontrado:
                for (lx, ly), s in self.historico_leituras.items():
                    if s['fedor']:
                        candidatos = []
                        for vx, vy in self.get_vizinhos(lx, ly):
                            if self.conhecimento[vy][vx] not in ['OK', 'P']:
                                descartado = False
                                for (olx, oly), os in self.historico_leituras.items():
                                    if (vx, vy) in self.get_vizinhos(olx, oly) and not os['fedor']:
                                        descartado = True
                                        break
                                if not descartado:
                                    candidatos.append((vx, vy))

                        if len(candidatos) == 1:
                            wx, wy = candidatos[0]
                            self.conhecimento[wy][wx] = 'W'
                            # Limpa qualquer suspeita de Wumpus residual no resto do mapa
                            for cy in range(4):
                                for cx in range(4):
                                    if (cx, cy) != (wx, wy) and self.conhecimento[cy][cx] == '?W':
                                        self.conhecimento[cy][cx] = '?'
                            mudou = True
                            break

            # 4. Dedução de Certeza de Poço por Unicidade
            for (lx, ly), s in self.historico_leituras.items():
                if s['brisa']:
                    candidatos = []
                    for vx, vy in self.get_vizinhos(lx, ly):
                        if self.conhecimento[vy][vx] not in ['OK', 'W']:
                            descartado = False
                            for (olx, oly), os in self.historico_leituras.items():
                                if (vx, vy) in self.get_vizinhos(olx, oly) and not os['brisa']:
                                    descartado = True
                                    break
                            if not descartado:
                                candidatos.append((vx, vy))

                    if len(candidatos) == 1:
                        px, py = candidatos[0]
                        if self.conhecimento[py][px] != 'P':
                            self.conhecimento[py][px] = 'P'
                            mudou = True

    def rota_segura_bfs(self, inicio, destino):
        queue = deque([[inicio]])
        visitados = {inicio}

        while queue:
            caminho = queue.popleft()
            atual = caminho[-1]

            if atual == destino:
                return caminho

            for vx, vy in self.get_vizinhos(atual[0], atual[1]):
                if (vx, vy) not in visitados:
                    if self.conhecimento[vy][vx] == 'OK':
                        visitados.add((vx, vy))
                        queue.append(caminho + [(vx, vy)])
        return None

    def exibir_mapa(self, pos_atual):
        print("\n===================================")
        print(f" MAPA DO MUNDO WUMPUS (4x4) - Pos Atual: {pos_atual}")
        print("===================================")
        for y in range(3, -1, -1):
            linha = f"{y} | "
            for x in range(4):
                if (x, y) == pos_atual:
                    linha += "🤖 "
                elif self.conhecimento[y][x] == 'W':
                    linha += "🦨 "  # Wumpus Confirmado
                elif self.conhecimento[y][x] == 'P':
                    linha += "🛑 "  # Poço Confirmado
                elif self.conhecimento[y][x] == '?W':
                    linha += "🟡 "  # Possível Wumpus (Suspeita)
                elif self.conhecimento[y][x] == '?P':
                    linha += "🔵 "  # Possível Poço (Suspeita)
                elif self.conhecimento[y][x] == 'OK':
                    if (x, y) in self.visitadas:
                        linha += "🟩 "  # Seguro e Visitado
                    else:
                        linha += "🟢 "  # Seguro e Não Visitado
                else:
                    linha += "⬛ "  # Desconhecido
            print(linha)
        print("    ----------------")
        print("     0  1  2  3 (X)\n")

    def executar(self):
        pos_atual = self.pos_robo
        caminho_total = [pos_atual]
        passo = 1

        while True:
            self.visitadas.add(pos_atual)
            fedor, brisa, brilho = self.ler_sensores(pos_atual[0], pos_atual[1])

            self.historico_leituras[pos_atual] = {'fedor': fedor, 'brisa': brisa}
            self.inferir_logica()

            sensores = []
            if fedor: sensores.append("FEDOR 🦨")
            if brisa: sensores.append("BRISA 💨")
            if brilho: sensores.append("BRILHO ✨ (OURO ENCONTRADO!)")

            txt_sensores = ", ".join(sensores) if sensores else "NENHUM"
            print(f"--- PASSO {passo} ---")
            print(f"📍 Robô em {pos_atual} | Sensores: {txt_sensores}")
            self.exibir_mapa(pos_atual)

            if brilho:
                print("🎉 SUCESSO! O Robô encontrou o Pote de Ouro com segurança!")
                break

            objetivos = []
            for y in range(4):
                for x in range(4):
                    if self.conhecimento[y][x] == 'OK' and (x, y) not in self.visitadas:
                        objetivos.append((x, y))

            if not objetivos:
                print("❌ NÃO HÁ CAMINHO SEGURO CONFIRMADO ATÉ O OURO!")
                print("A IA interrompeu a movimentação para evitar riscos de falha/morte.")
                break

            melhor_rota = None
            for obj in objetivos:
                rota = self.rota_segura_bfs(pos_atual, obj)
                if rota:
                    if melhor_rota is None or len(rota) < len(melhor_rota):
                        melhor_rota = rota

            if not melhor_rota or len(melhor_rota) < 2:
                print("❌ Não foi possível traçar uma rota segura.")
                break

            pos_atual = melhor_rota[1]
            caminho_total.append(pos_atual)
            passo += 1

        print("\n==================================================")
        print("CAMINHO PERCORRIDO PELO ROBÔ:")
        print(" -> ".join([str(p) for p in caminho_total]))
        print("==================================================")


# --- LEITURA E INICIALIZAÇÃO ---

def ler_coordenada(msg):
    while True:
        try:
            val = input(msg).strip()
            x, y = map(int, val.split(','))
            if 0 <= x < 4 and 0 <= y < 4:
                return (x, y)
            print("⚠️ Digite coordenadas entre 0 e 3.")
        except ValueError:
            print("⚠️ Formato inválido! Use X,Y.")

def main():
    print("==========================================")
    print("   DESAFIO DO LABIRINTO WUMPUS 4x4 (IA)   ")
    print("==========================================")
    print("Escolha o modo de inicialização:")
    print("1 - Inserir posições customizadas")
    print("2 - Gerar posições aleatórias")
    
    opcao = input("Opção (1/2, padrão=2): ").strip()
    
    if opcao == "1":
        print("\nDigite as coordenadas no formato X,Y (valores de 0 a 3):")
        pos_robo = ler_coordenada("Posição Inicial do Robô (X,Y): ")
        pos_ouro = ler_coordenada("Posição do Ouro (X,Y): ")
        pos_wumpus = ler_coordenada("Posição do Wumpus (X,Y): ")
        poco1 = ler_coordenada("Posição do Poço 1 (X,Y): ")
        poco2 = ler_coordenada("Posição do Poço 2 (X,Y): ")
        pocos = [poco1, poco2]
    else:
        pos = random.sample([(x, y) for x in range(4) for y in range(4)], 5)
        pos_robo, pos_ouro, pos_wumpus = pos[0], pos[1], pos[2]
        pocos = [pos[3], pos[4]]

    jogo = MundoWumpus(pos_robo, pos_ouro, pos_wumpus, pocos)
    jogo.executar()

if __name__ == "__main__":
    main()