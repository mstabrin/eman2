#include "marchingcubes.h"

static const int a2fVertexOffset[8][3] =
{
		{0, 0, 0},{1, 0, 0},{1, 1, 0},{0, 1, 0},
		{0, 0, 1},{1, 0, 1},{1, 1, 1},{0, 1, 1}
};

