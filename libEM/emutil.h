/**
 * $Id$
 */
#ifndef eman__emutil__h__
#define eman__emutil__h__ 1

#include "emobject.h"
#include <string>
#include <vector>

using std::string;
using std::vector;

namespace EMAN
{
	class ImageIO;
	class Region;

	class EMUtil
	{
	  public:
		enum EMDataType
		{
			EM_CHAR,
			EM_UCHAR,
			EM_SHORT,
			EM_USHORT,
			EM_INT,
			EM_UINT,
			EM_FLOAT,
			EM_DOUBLE,
			EM_SHORT_COMPLEX,
			EM_USHORT_COMPLEX,
			EM_FLOAT_COMPLEX,
			EM_UNKNOWN
		};

		enum ImageType
		{
			IMAGE_MRC,
			IMAGE_SPIDER,
			IMAGE_SINGLE_SPIDER,
			IMAGE_IMAGIC,
			IMAGE_HDF,
			IMAGE_DM3,
			IMAGE_TIFF,
			IMAGE_PGM,
			IMAGE_LST,
			IMAGE_PIF,
			IMAGE_VTK,
			IMAGE_PNG,
			IMAGE_SAL,
			IMAGE_ICOS,
			IMAGE_EMIM,
			IMAGE_GATAN2,
			IMAGE_AMIRA,
			IMAGE_XPLOR,
			IMAGE_EM,
			IMAGE_UNKNOWN
		};

		static EMData *vertical_acf(const EMData * image, int maxdy);

		static EMData *make_image_median(const vector < EMData * >&image_list);

		static ImageType get_image_ext_type(string file_ext);
		static ImageType get_image_type(string filename);
		static int get_image_count(string filename);
		static ImageIO *get_imageio(string filename, int rw_mode, ImageType image_type =
									IMAGE_UNKNOWN);

		static const char *get_imagetype_name(EMUtil::ImageType type);
		static const char *get_datatype_string(EMDataType type);

		static void get_region_dims(const Region * area, int nx, int *area_x, int ny,
									int *area_y, int nz = 1, int *area_z = 0);

		static void get_region_origins(const Region * area, int *p_x0, int *p_y0, int *p_z0 = 0,
									   int nz = 1, int image_index = 0);

		static int get_region_data(unsigned char *cdata, FILE * in, int image_index,
								   size_t mode_size, int nx, int ny, int nz = 1,
								   const Region * area = 0, bool need_flip = false,
								   int pre_row = 0, int post_row = 0);

		static void dump_dict(const Dict & dict);

		static bool is_same_size(const EMData * image1, const EMData * image2);
		static bool is_same_ctf(const EMData * image1, const EMData * image2);

	  private:
		static ImageType fast_get_image_type(string filename, const void *first_block,
											 off_t file_size);
	};


	class UnknownImageFormat : public Exception
	{
	public:
		UnknownImageFormat(const string& imagename, const string& file = "unknown",
						   int line = 0, const string& desc = "")
			: Exception(file, line, desc, imagename) {}
	};

	class ImageHeaderReadError : public Exception
	{
	public:
		ImageHeaderReadError(const string& imagename, const string& file = "unknown",
							 int line = 0, const string& desc = "")
			: Exception(file, line, desc, imagename) {}
	};
	
	class ImageDataReadError : public Exception
	{
	public:
		ImageDataReadError(const string& imagename, const string& file = "unknown",
						   int line = 0, const string& desc = "")
			: Exception(file, line, desc, imagename) {}
	};


	class ImageHeaderWriteError : public Exception
	{
	public:
		ImageHeaderWriteError(const string& imagename, const string& file = "unknown",
							 int line = 0, const string& desc = "")
			: Exception(file, line, desc, imagename) {}
	};
	
	class ImageDataWriteError : public Exception
	{
	public:
		ImageDataWriteError(const string& imagename, const string& file = "unknown",
						   int line = 0, const string& desc = "")
			: Exception(file, line, desc, imagename) {}
	};

	class NotSameImageSizeError : public Exception
	{
	public:
		NotSameImageSizeError(const string& file = "unknown",
							  int line = 0, const string& desc = "")
			: Exception(file, line, desc) {}
	};

	class NotSquareImageError : public Exception
	{
	public:
		NotSquareImageError(const string& file = "unknown",
							int line = 0, const string& desc = "")
			: Exception(file, line, desc) {}
	};

	class ImageDimError : public Exception
	{
	public:
		ImageDimError(const string& file = "unknown",
					  int line = 0, const string& desc = "")
			: Exception(file, line, desc) {}
	};

	class NullEMDataObjectError : public Exception
	{
	public:
		NullEMDataObjectError(const string& file = "unknown",
							  int line = 0, const string& desc = "")
			: Exception(file, line, desc) {}
	};
	
	class ShrinkFactorError : public Exception
	{
	public:
		ShrinkFactorError(int sf, const string& file = "unknown",
						  int line = 0, const string& desc = "")
			: Exception(file, line, desc)
		{
			char s[32];
			sprintf(s, "%d", sf);
			set_objname(string(s));
		}
	};

	class InvalidModeError : public Exception
	{
	public:
		InvalidModeError(int low_mode, int high_mode, int wrong_mode,
						 const string& file = "unknown",
						 int line = 0, const string& desc = "")
			: Exception(file, line, desc)
		{
			char s[128];
			sprintf(s, "mode %d out of range [%d,%d]",
					wrong_mode, low_mode, high_mode);
			set_objname(string(s));
		}
	};
					

	
}

#endif
