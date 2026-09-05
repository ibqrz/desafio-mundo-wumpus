import random
from collections import deque
import sys

class MundoWumpus:
    def __init__(self, pos_robo, pos_ouro, pos_wumpus, pocos):
        self.tamanho = 4
        self.pos_robo = pos_robo
        self.pos_ouro = pos_ouro
        self.pos_wumpus = pos_wumpus
        self.pocos = pocos

        # Matriz de Conhecimento:
        # '?'  = Desconhecido (⬛)
        # 'OK' = Seguro (🟢 não visitado / 🟩 visitado)
        # '?W' = Possível Wumpus (🟡)
        # '?P' = Possível Poço (🔵)
        # '?WP'= Possível Wumpus e Poço simultâneo (🌐)
        # 'W'  = Wumpus Confirmado (🦨)
        # 'P'  = Poço Confirmado (🛑)
        self.conhecimento = [['?' for _ in range(4)] for _ in range(4)]
        self.visitadas = set()
        self.historico_leituras = {}
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
        """
        Motor de Inferência com Explicação de Sensores por Perigos Confirmados.
        """
        # 1. Salas visitadas são sempre 'OK'
        for (lx, ly) in self.historico_leituras.keys():
            self.conhecimento[ly][lx] = 'OK'

        wumpus_confirmado = None
        for y in range(4):
            for x in range(4):
                if self.conhecimento[y][x] == 'W':
                    wumpus_confirmado = (x, y)

        pocos_confirmados = [(x, y) for y in range(4) for x in range(4) if self.conhecimento[y][x] == 'P']

        # 2. Dedução por Unicidade de Vizinhança
        for (lx, ly), s in self.historico_leituras.items():
            vizs = self.get_vizinhos(lx, ly)

            if s['fedor'] and wumpus_confirmado is None:
                candidatos_w = [v for v in vizs if self.conhecimento[v[1]][v[0]] not in ['OK', 'P']]
                if len(candidatos_w) == 1:
                    wx, wy = candidatos_w[0]
                    self.conhecimento[wy][wx] = 'W'
                    wumpus_confirmado = (wx, wy)

            if s['brisa'] and len(pocos_confirmados) < 2:
                candidatos_p = [v for v in vizs if self.conhecimento[v[1]][v[0]] not in ['OK', 'W']]
                if len(candidatos_p) == 1:
                    px, py = candidatos_p[0]
                    if self.conhecimento[py][px] != 'P':
                        self.conhecimento[py][px] = 'P'
                        if (px, py) not in pocos_confirmados:
                            pocos_confirmados.append((px, py))

        # Atualiza lista de poços após deduções
        pocos_confirmados = [(x, y) for y in range(4) for x in range(4) if self.conhecimento[y][x] == 'P']

        # 3. Regra de Explicação / Satisfação de Sensor:
        # Se uma leitura sentiu brisa e já existe um poço confirmado adjacente,
        # o outro vizinho desconhecido não precisa ser poço para justificar a brisa.
        for (lx, ly), s in self.historico_leituras.items():
            vizs = self.get_vizinhos(lx, ly)
            if s['brisa']:
                tem_poco_confirmado = any(self.conhecimento[v[1]][v[0]] == 'P' for v in vizs)
                if tem_poco_confirmado:
                    for vx, vy in vizs:
                        if self.conhecimento[vy][vx] == '?P':
                            self.conhecimento[vy][vx] = 'OK'
            if s['fedor']:
                tem_wumpus_confirmado = any(self.conhecimento[v[1]][v[0]] == 'W' for v in vizs)
                if tem_wumpus_confirmado:
                    for vx, vy in vizs:
                        if self.conhecimento[vy][vx] == '?W':
                            self.conhecimento[vy][vx] = 'OK'
                        elif self.conhecimento[vy][vx] == '?WP':
                            self.conhecimento[vy][vx] = '?P'

        # Dedução lógica extra para poços por exclusão de vizinho único
        for (lx, ly), s in self.historico_leituras.items():
            if s['brisa'] and len(pocos_confirmados) < 2:
                vizs = self.get_vizinhos(lx, ly)
                desconhecidos = [v for v in vizs if self.conhecimento[v[1]][v[0]] not in ['OK', 'W', 'P']]
                if len(desconhecidos) == 1:
                    ux, uy = desconhecidos[0]
                    if self.conhecimento[uy][ux] != 'P':
                        self.conhecimento[uy][ux] = 'P'
                        if (ux, uy) not in pocos_confirmados:
                            pocos_confirmados.append((ux, uy))

        pocos_confirmados = [(x, y) for y in range(4) for x in range(4) if self.conhecimento[y][x] == 'P']

        # 4. Refinação e Atribuição Dinâmica de Estados e Suspeitas (?WP, ?W, ?P, OK)
        for y in range(4):
            for x in range(4):
                if self.conhecimento[y][x] in ['W', 'P', 'OK']:
                    continue

                tem_viz_fedor = any((x, y) in self.get_vizinhos(lx, ly) and s['fedor'] for (lx, ly), s in self.historico_leituras.items())
                tem_viz_brisa = any((x, y) in self.get_vizinhos(lx, ly) and s['brisa'] for (lx, ly), s in self.historico_leituras.items())

                provado_sem_fedor = any((x, y) in self.get_vizinhos(lx, ly) and not s['fedor'] for (lx, ly), s in self.historico_leituras.items())
                provado_sem_brisa = any((x, y) in self.get_vizinhos(lx, ly) and not s['brisa'] for (lx, ly), s in self.historico_leituras.items())

                if provado_sem_fedor:
                    tem_viz_fedor = False
                if provado_sem_brisa:
                    tem_viz_brisa = False

                if wumpus_confirmado is not None:
                    tem_viz_fedor = False

                if len(pocos_confirmados) >= 2:
                    tem_viz_brisa = False

                if tem_viz_fedor and tem_viz_brisa:
                    self.conhecimento[y][x] = '?WP'
                elif tem_viz_fedor:
                    self.conhecimento[y][x] = '?W'
                elif tem_viz_brisa:
                    self.conhecimento[y][x] = '?P'
                else:
                    tem_info = any((x, y) in self.get_vizinhos(lx, ly) for (lx, ly) in self.historico_leituras.keys())
                    if tem_info or self.conhecimento[y][x] in ['?WP', '?W', '?P']:
                        self.conhecimento[y][x] = 'OK'

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
                    linha += "🦨 "
                elif self.conhecimento[y][x] == 'P':
                    linha += "🛑 "
                elif self.conhecimento[y][x] == '?WP':
                    linha += "🌐 "
                elif self.conhecimento[y][x] == '?W':
                    linha += "🟡 "
                elif self.conhecimento[y][x] == '?P':
                    linha += "🔵 "
                elif self.conhecimento[y][x] == 'OK':
                    if (x, y) in self.visitadas:
                        linha += "🟩 "
                    else:
                        linha += "🟢 "
                else:
                    linha += "⬛ "
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
    
    try:
        opcao = input("Opção (1/2, padrão=2): ").strip()
    except Exception:
        opcao = "2"
    
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
        print(f"Gerado automaticamente -> Robô: {pos_robo}, Ouro: {pos_ouro}, Wumpus: {pos_wumpus}, Poços: {pocos}")

    jogo = MundoWumpus(pos_robo, pos_ouro, pos_wumpus, pocos)
    jogo.executar()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ocorreu um erro inesperado: {e}")
    finally:
        input("\nPressione ENTER para fechar a janela...")