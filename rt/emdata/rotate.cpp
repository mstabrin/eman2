#include "emdata.h"
#include <math.h>

using namespace EMAN;

const char* get_test_image()
{
	static char filename[256];
	static bool done = false;
	if (!done) {
		sprintf(filename, "%s/images/groel3d.mrc", getenv("HOME"));
		done = true;
	}
	return filename;
}
/*
[(0, 0, 0), (0, 0, 45), (0, 0, 90), (0, 0, 135), (0, 0, 180), (0, 0, 225),
(0, 0, 270), (0, 0, 315), (45, 0, 0), (45, 0, 45), (45, 0, 90), (45, 0,
135), (45, 0, 180), (45, 0, 225), (45, 0, 270), (45, 0, 315), (45, 90, 0),
(45, 90, 45), (45, 90, 90), (45, 90, 135), (45, 90, 180), (45, 90, 225),
(45, 90, 270), (45, 90, 315), (45, 180, 0), (45, 180, 45), (45, 180, 90),
(45, 180, 135), (45, 180, 180), (45, 180, 225), (45, 180, 270), (45, 180,
315), (45, 270, 0), (45, 270, 45), (45, 270, 90), (45, 270, 135), (45,
270, 180), (45, 270, 225), (45, 270, 270), (45, 270, 315), (90, 0, 0),
(90, 0, 45), (90, 0, 90), (90, 0, 135), (90, 0, 180), (90, 0, 225), (90,
0, 270), (90, 0, 315), (90, 60, 0), (90, 60, 45), (90, 60, 90), (90, 60,
135), (90, 60, 180), (90, 60, 225), (90, 60, 270), (90, 60, 315), (90,
120, 0), (90, 120, 45), (90, 120, 90), (90, 120, 135), (90, 120, 180),
(90, 120, 225), (90, 120, 270), (90, 120, 315), (90, 180, 0), (90, 180,
45), (90, 180, 90), (90, 180, 135), (90, 180, 180), (90, 180, 225), (90,
180, 270), (90, 180, 315), (90, 240, 0), (90, 240, 45), (90, 240, 90),
(90, 240, 135), (90, 240, 180), (90, 240, 225), (90, 240, 270), (90, 240,
315), (90, 300, 0), (90, 300, 45), (90, 300, 90), (90, 300, 135), (90,
300, 180), (90, 300, 225), (90, 300, 270), (90, 300, 315), (135, 0, 0),
(135, 0, 45), (135, 0, 90), (135, 0, 135), (135, 0, 180), (135, 0, 225),
(135, 0, 270), (135, 0, 315), (135, 90, 0), (135, 90, 45), (135, 90, 90),
(135, 90, 135), (135, 90, 180), (135, 90, 225), (135, 90, 270), (135, 90,
315), (135, 180, 0), (135, 180, 45), (135, 180, 90), (135, 180, 135),
(135, 180, 180), (135, 180, 225), (135, 180, 270), (135, 180, 315), (135,
270, 0), (135, 270, 45), (135, 270, 90), (135, 270, 135), (135, 270, 180),
(135, 270, 225), (135, 270, 270), (135, 270, 315), (180, 0, 0), (180, 0,
45), (180, 0, 90), (180, 0, 135), (180, 0, 180), (180, 0, 225), (180, 0,
270), (180, 0, 315)]
*/

void rotate(EMData * image, float alt, float az, float phi)
{
	char outfile[128];
	sprintf(outfile, "test_%d_%d_%d.mrc", (int)alt, (int)az, (int)phi);
	float f = (float)M_PI / 180;
	const char* imagefile = get_test_image();
	image->read_image(imagefile);
	image->rotate(alt*f, az*f, phi*f);
	image->write_image(outfile, 0, EMUtil::IMAGE_MRC);
}

int main()
{
	int err = 0;
	
	EMData *image = new EMData();
#if 0
	for (int i = 0; i <= 180; i += 45) {
		for (int j = 0; j < 360; j += 60) {
			for (int z = 0; z < 360; z += 45) {
				rotate(image, i, j, z);
			}
		}
	}
#endif

	rotate(image, 135, 0, 0);

	delete image;
	image = 0;
	
	return  err;
}
