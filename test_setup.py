import os

def create_dummies():
    os.makedirs("test_music/rock", exist_ok=True)
    os.makedirs("test_music/jazz", exist_ok=True)
    
    files = [
        "test_music/rock/Linkin Park - Numb.mp3",
        "test_music/rock/Metallica - Enter Sandman.mp3",
        "test_music/jazz/Miles Davis - So What.mp3",
        "test_music/jazz/John Coltrane - Giant Steps.mp3",
        "test_music/Happy Song.mp3",
        "test_music/Sad Song.mp3"
    ]
    
    for f in files:
        with open(f, 'w') as file:
            file.write("dummy content")
            
    print("Created dummy music files.")

if __name__ == "__main__":
    create_dummies()
