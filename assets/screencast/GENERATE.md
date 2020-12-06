# Generate Gif from Video

`ffmpeg -i normcap_demo.mp4 -r 8 -vf "scale=825:-1,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" normcap.gif`
