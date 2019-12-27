import struct, os, sys, math
from PIL import Image

#CONSTANTS
 
FILE_OUTPUT_NAME = "output.Civ5Map"

def main():
    file = open("flat-8080.Civ5Map", "rb")

    mapLoaderInstance = Maploader(file)

class Maploader():
    def __init__(self, file):
        self.m_File = file

        self.loadImage()
        self.optionalLoad()

    def loadImage(self):
        try:
            path = len(sys.argv) > 1 and sys.argv[1] or input("Please enter the image path (prefer .jpg/.jpeg): ")
            self.img = Image.open(path)
            self.img = self.img.rotate(180)
            self.img = self.img.transpose(Image.FLIP_LEFT_RIGHT)
        except IOError:
            print("(IOError) Invalid file.")
            exit()
        finally:
            self.rbg = self.img.convert("RGB")
            self.getMaxSize()

    def getMaxSize(self):
        try:
            size = len(sys.argv) > 2 and sys.argv[2] or input("Please enter max width: ")
            self.selected = int(size)
        
        except IOError:
            print("(IOError) Invalid file.")
            exit()
        finally:
            if type(self.selected) and self.selected <= 128:
                print("Accepted size.")
            else:
                print("Invalid size.")

    def optionalLoad(self):
        

        # get image info

        width, height = self.img.size

        ratio = width/height

        self.m_InfoByte = self.m_File.read(1)

        self.m_Width = math.floor(self.selected)
        self.m_Height = math.floor(self.m_Width/ratio)

        self.m_File.seek(9)
        first_bytes = self.m_File.read(0x506 - 9)
        
        #self.m_Width =  min(120, math.floor(self.m_Width * ratio))

        map_bytes = bytes()

        pixel_per_width = width/self.m_Width
        pixel_per_height = height/self.m_Height
        
        # 0 = TERRAIN_GRASS
        # 1 = TERRAIN_PLAINS
        # 2 = TERRAIN_DESERT
        # 3 = TERRAIN_TUNDRA
        # 4 = TERRAIN_SNOW
        # 5 = TERRAIN_COAST
        # 6 = TERRAIN_OCEAN

        for y in range(self.m_Height):
            for x in range(self.m_Width):
                # Image sector
                leftX = x*pixel_per_width
                leftY = y*pixel_per_height
                rightX = leftX + pixel_per_width
                rightY = leftY + pixel_per_height

                temp = self.img.crop((leftX, leftY, rightX, rightY))
                temp.load()
                temp = temp.resize((1,1), Image.ANTIALIAS)
                r, g, b = temp.getpixel((0, 0))
                
                #define areaType by RBG-Values
                areaType = 6

                if r > 220 and g > 220 and b > 220:
                    areaType = 4
                elif r > 100 and g > 100 and b > 100 and r < 150 and g < 150 and b < 150:
                    areaType = 5
                elif g > 130 and r > 130 and g < 200:
                    areaType = 1
                elif r>170 and g>170 and b < 200:
                    areaType = 4
                elif r < 20 and g < 20 and b < 20:
                    areaType = 1
                elif r+g<b+70:
                    areaType = 6
                else:
                    areaType = 0
                #write terrain-hex-infos

                tempBytes = bytearray.fromhex("00 06 FF FF 00 00 00 FF")

                tempBytes[1] = areaType

                self.m_File.read(8)
                map_bytes += bytes(tempBytes)


        self.m_File.seek(0xCD06)
        size = os.path.getsize("./flat-8080.Civ5Map")
        second_bytes = self.m_File.read(size - self.m_File.tell())

        self.m_File.close()
        
        with open(FILE_OUTPUT_NAME, "wb") as f:
            f.write(self.m_InfoByte)
            f.write(struct.pack("<i", self.m_Width))
            f.write(struct.pack("<i", self.m_Height))
            f.write(first_bytes)
            f.write(map_bytes)
            f.write(second_bytes)
            # add additional scenario space otherwise the map will not load within the map-editor
            # normally a field has bytes(8) information but due to the fact that the base-file is 80*80
            # we only need to generate bytes(4) for every extra field due to a maximal size of 128*80 (GIANT)
            if self.m_Width*self.m_Height > 80*80:
                for x in range(self.m_Width*self.m_Height - 80*80):
                    f.write(struct.pack("<II", 4294967295, 4294967295)) 

        print("Generated map with Width %d and height %d to file %s." % (self.m_Width, self.m_Height, FILE_OUTPUT_NAME))


main()
