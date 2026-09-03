# Labirinto Wumpus

Unianchieta - Inteligência Artificial


## :triangular_flag_on_post: Desafio:

### 1. Descrição do Problema

O robô deve navegar em uma caverna representada por uma grade 4 × 4. Diferente do jogo clássico parcialmente observável, o seu algoritmo receberá o mapa completo no momento da execução e deverá calcular a melhor rota que leve o robô do ponto de partida até o ouro, evitando perigos mortais (o Wumpus e 2 poços).

### 2. Requisitos do Código Python

O programa deve ser escrito em Python puro (sem necessidade de bibliotecas externas complexas) e seguir a seguinte especificação:

Entrada de Dados: O script deve solicitar ou receber como parâmetros:
Posição inicial do robô (ex: (0, 0))
Posição do Ouro / Tesouro (ex: (2, 3))
Posição do Wumpus (ex: (0, 2))
Posições dos 2 Poços (ex: (1, 1) e (3, 1))

Regras de Movimentação: O robô só pode se mover para salas adjacentes (Cima, Baixo, Esquerda, Direita) dentro dos limites 4 × 4.

Restrições Mortais: Entrar na sala do Wumpus ou em qualquer um dos Poços resulta em falha automática.

Saída do Programa:
Se existir um caminho seguro, imprimir a sequência ordenada de coordenadas que o robô deve percorrer da origem até o ouro (ex: (0,0) -> (1,0) -> (2,0) -> (2,1) -> (2,2) -> (2,3)). Se o mapa for impossível (ouro bloqueado por poços/Wumpus), imprimir uma mensagem informando que não há caminho seguro.


// :dart:
