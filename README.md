# Space Oddisey

A multiplayer spaceship movement game built with Pygame, featuring player score tracking and real-time ping display for connected peers.

## Features

- Control your spaceship using arrow keys.
- Real-time display of your score and other players’ scores.
- Shows network latency (ping) for each connected player.
- Countdown timer for game duration (default 60 seconds).
- Final score summary displayed at the end of the game.

## Installation

1. Make sure you have Python 3.x installed.
2. Install Pygame:

```bash
pip install pygame
```

## How to Play
To start, each player simply run:
```bash
python peer.py
```
to join the game.

Control your spaceship with the arrow keys:
- Left: Move left
- Right: Move right 
- Up: Move up 
- Down: Move down
The game will run for 60 seconds by default, then display the final scores.

### Game Objective
- You play as a triangle-shaped spaceship. 
- The goal is to collect as many randomly generated circles as possible within 60 seconds. 
- Other players are shown as beige-colored circles, and everyone can see each other/and each other's scores in real time. 
- The game ends after one minute, and the final scores are displayed for all peers.

---
## Gameplay Demo

Watch the gameplay here:  
[https://youtu.be/K16kKveTV4U?si=9RB9DCtUGPrVSBkc](https://youtu.be/K16kKveTV4U?si=9RB9DCtUGPrVSBkc)
---
## Peer-to-Peer Networking Architecture
This game is fully peer-to-peer (P2P)—there is no server involved at any stage.
1. Peer Discovery & Connection
   - At game startup, each peer broadcasts on the same local IP and port, announcing its presence by sending its manually entered port number. 
   - Peers collect these port numbers and establish direct connections with each other.
2. Host Election & Game Coordination
   - After discovery, each peer generates a random number and shares it with others.
   - The peer with the highest random number becomes the host, responsible for:
   - Generating and synchronizing the locations of collectible circles (shared game objects). 
   - Ensuring all connected peers are up-to-date with the game state. 
   - If the host disconnects, a re-election process is automatically triggered, and a new host is chosen based on the same logic. 
   - This ensures continuous gameplay without central coordination and graceful recovery from disconnections.
3. Multi-Game Support
   - If a player starts the game while others are already playing, a new room is automatically created.
   - This allows multiple, independent games to run simultaneously on the same LAN, with each group of peers managing their own connections and gameplay state.

## Networking Compliance
- UDP Protocol
- Peer-to-Peer Architecture. Each client exchanges messages directly with peers.
- The game handles disconnects gracefully.
- Peers Scan local network (e.g., 192.168.x.x) to detect available players.

### Algorithmic Considerations
- Dead reckoning: was evaluated but not implemented, as player movement in this game is short-term and manually controlled (not continuous in one direction at constant speed). Predicting future positions without updates did not improve the smoothness or reduce load meaningfully, so we kept real-time updates without extrapolation.
- Ping Arbitration: A win condition is implemented:
The spaceship that collects the most circles within 60 seconds is declared the winner.
- Interest Management: The game limits packet sending only to known, active peers. Each player only sends data to discovered and connected players, minimizing unnecessary network traffic.
No global broadcasting is used, aligning with peer-specific relevance in a LAN environment.