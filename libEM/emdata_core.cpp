/**
 * $Id$
 */
 
/*
 * Author: Steven Ludtke, 04/10/2003 (sludtke@bcm.edu)
 * Copyright (c) 2000-2006 Baylor College of Medicine
 * 
 * This software is issued under a joint BSD/GNU license. You may use the
 * source code in this file under either license. However, note that the
 * complete EMAN2 and SPARX software packages have some GPL dependencies,
 * so you are responsible for compliance with the licenses of these packages
 * if you opt to use BSD licensing. The warranty disclaimer below holds
 * in either instance.
 * 
 * This complete copyright notice must be included in any revised version of the
 * source code. Additional authorship citations may be added, but existing
 * author citations must be preserved.
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 * 
 * */
 
#include "emdata.h" 
#include "ctf.h"
#include "emfft.h"
#include "cmp.h"

using namespace EMAN;

// debug only
#include <iostream>
#include <cstring>
using std::cout;
using std::endl;

void EMData::free_memory()
{
	ENTERFUNC;

	if (rdata) {
		free(rdata);
		rdata = 0;
	}

	if (supp) {
		free(supp);
		supp = 0;
	}
	
	if (rot_fp != 0)
	{
		delete rot_fp;
		rot_fp = 0;
	}

	EXITFUNC;
}

EMData * EMData::copy() const
{
	ENTERFUNC;
	
	EMData *ret = new EMData(*this);

	EXITFUNC;
	return ret;
}


EMData *EMData::copy_head() const
{
	ENTERFUNC;
	EMData *ret = new EMData();
	ret->attr_dict = attr_dict;
	ret->set_size(nx, ny, nz);

	ret->flags = flags;

	ret->all_translation = all_translation;

	ret->path = path;
	ret->pathnum = pathnum;

// should these be here? d.woolford I did not comment them out, merely place them here (commented out) to draw attention
// 	ret->xoff = xoff;
// 	ret->yoff = yoff;
// 	ret->zoff = zoff;
// 	ret->changecount = changecount;

	ret->update();

	EXITFUNC;
	return ret;
}

void EMData::add(float f,int keepzero)
{
	ENTERFUNC;

	if( is_real() )
	{
		if (f != 0) {
			update();
			size_t size = nxy * nz;
			if (keepzero) {
				for (size_t i = 0; i < size; i++) {
					if (rdata[i]) rdata[i] += f;
				}
			}
			else {
				for (size_t i = 0; i < size; i++) {
					rdata[i] += f;
				}
			}
		}
	}
	else if( is_complex() )
	{
		if( f!=0 )
		{
			update();
			size_t size = nx*ny*nz; //size of data
			if( keepzero )
			{
				for(size_t i=0; i<size; i+=2)
				{
					if (rdata[i]) rdata[i] += f;
				}
			}
			else
			{
				for(size_t i=0; i<size; i+=2)
				{
					rdata[i] += f;
				}
			}
		}
	}
	else
	{
		throw ImageFormatException("This image is neither a real nor a complex image.");
	}
	update();
	EXITFUNC;
}


//for add operation, real and complex image is the same
void EMData::add(const EMData & image)
{
	ENTERFUNC;
	if (nx != image.get_xsize() || ny != image.get_ysize() || nz != image.get_zsize()) {
		throw ImageFormatException( "images not same sizes");
	}
	else if( (is_real()^image.is_real()) == true )
	{
		throw ImageFormatException( "not support add between real image and complex image");
	}
	else {
		
		const float *src_data = image.get_data();
		int size = nxy * nz;

		for (int i = 0; i < size; i++) {
			rdata[i] += src_data[i];
		}
		update();
	}
	EXITFUNC;
}


void EMData::sub(float f)
{
	ENTERFUNC;

	if( is_real() )
	{
		if (f != 0) {
			update();
			size_t size = nxy * nz;
			for (size_t i = 0; i < size; i++) {
				rdata[i] -= f;
			}
		}
	}
	else if( is_complex() )
	{
		if( f != 0 )
		{
			update();
			size_t size = nxy * nz;
			for( size_t i=0; i<size; i+=2 )
			{
				rdata[i] -= f;
			}
		}
	}
	else
	{
		throw ImageFormatException("This image is neither a real nor a complex image.");
	}

	EXITFUNC;
}


//for sub operation, real and complex image is the same
void EMData::sub(const EMData & em)
{
	ENTERFUNC;

	if (nx != em.get_xsize() || ny != em.get_ysize() || nz != em.get_zsize()) {
		throw ImageFormatException("images not same sizes");
	}
	else if( (is_real()^em.is_real()) == true )
	{
		throw ImageFormatException( "not support sub between real image and complex image");
	}
	else {
		update();
		const float *src_data = em.get_data();
		size_t size = nxy * nz;

		for (size_t i = 0; i < size; i++) {
			rdata[i] -= src_data[i];
		}
	}
	EXITFUNC;
}


void EMData::mult(float f)
{
	ENTERFUNC;

	if (is_complex()) {
		ap2ri();
	}
	if (f != 1.0) {
		update();
		size_t size = nxy * nz;
		for (size_t i = 0; i < size; i++) {
			rdata[i] *= f;
		}
	}
	EXITFUNC;
}


void EMData::mult(const EMData & em, bool prevent_complex_multiplication)
{
	ENTERFUNC;

	if (nx != em.get_xsize() || ny != em.get_ysize() || nz != em.get_zsize()) {
		throw ImageFormatException( "can not multiply images that are not the same size");
	}
	else if( (is_real()^em.is_real()) == true )
	{
		throw ImageFormatException( "can not multiply real and complex images.");
	}
	else
	{
		update();
		const float *src_data = em.get_data();
		size_t size = nxy * nz;
		if( is_real() || prevent_complex_multiplication )
		{
			for (size_t i = 0; i < size; i++) {
				rdata[i] *= src_data[i];
			}
		}
		else
		{
			typedef std::complex<float> comp;
			for( size_t i = 0; i < size; i+=2 )
			{
				comp c_src( src_data[i], src_data[i+1] );
				comp c_rdat( rdata[i], rdata[i+1] );
				comp c_result = c_src * c_rdat;
				rdata[i] = c_result.real();
				rdata[i+1] = c_result.imag();
			}
		}
	}

	EXITFUNC;
}


void EMData::div(float f)
{
	ENTERFUNC;

	if (is_complex()) {
		ap2ri();
	}
	
	if (f != 0) {
		update();
		size_t size = nxy * nz;
		for (size_t i = 0; i < size; i++) {
			rdata[i] /= f;
		}
	}
	else {
		throw InvalidValueException(f, "divide by zero");
	}
	EXITFUNC;
}


void EMData::div(const EMData & em)
{
	ENTERFUNC;

	if (nx != em.get_xsize() || ny != em.get_ysize() || nz != em.get_zsize()) {
		throw ImageFormatException( "images not same sizes");
	}
	else if( (is_real()^em.is_real()) == true )
	{
		throw ImageFormatException( "not support division between real image and complex image");
	}
	else {
		update();
		const float *src_data = em.get_data();
		size_t size = nxy * nz;

		if( is_real() )
		{
			for (size_t i = 0; i < size; i++) {
				if(src_data[i] != 0) {
					rdata[i] /= src_data[i];
				}
				else {
					throw InvalidValueException(src_data[i], "divide by zero");
				}
			}
		}
		else
		{
			typedef std::complex<float> comp;
			for( size_t i = 0; i < size; i+=2 )
			{
				comp c_src( src_data[i], src_data[i+1] );
				comp c_rdat( rdata[i], rdata[i+1] );
				comp c_result = c_rdat / c_src;
				rdata[i] = c_result.real();
				rdata[i+1] = c_result.imag();
			}
		}
	}

	EXITFUNC;
}


// just a shortcut for cmp("dot")
float EMData::dot(EMData * with)
{
	ENTERFUNC;
	if (!with) {
		throw NullPointerException("Null EMData Image");
	}
	DotCmp dot_cmp;
	float r = -dot_cmp.cmp(this, with);
	EXITFUNC;
	return r;
}


EMData *EMData::get_row(int row_index) const
{
	ENTERFUNC;

	if (get_ndim() > 2) {
		throw ImageDimensionException("1D/2D image only");
	}

	EMData *ret = new EMData();
	ret->set_size(nx, 1, 1);
	memcpy(ret->get_data(), get_data() + nx * row_index, nx * sizeof(float));
	ret->update();
	EXITFUNC;
	return ret;
}


void EMData::set_row(const EMData * d, int row_index)
{
	ENTERFUNC;

	if (get_ndim() > 2) {
		throw ImageDimensionException("1D/2D image only");
	}
	if (d->get_ndim() != 1) {
		throw ImageDimensionException("1D image only");
	}

	float *dst = get_data();
	float *src = d->get_data();
	memcpy(dst + nx * row_index, src, nx * sizeof(float));
	update();
	EXITFUNC;
}

EMData *EMData::get_col(int col_index) const
{
	ENTERFUNC;

	if (get_ndim() != 2) {
		throw ImageDimensionException("2D image only");
	}

	EMData *ret = new EMData();
	ret->set_size(ny, 1, 1);
	float *dst = ret->get_data();
	float *src = get_data();

	for (int i = 0; i < ny; i++) {
		dst[i] = src[i * nx + col_index];
	}

	ret->update();
	EXITFUNC;
	return ret;
}


void EMData::set_col(const EMData * d, int n)
{
	ENTERFUNC;

	if (get_ndim() != 2) {
		throw ImageDimensionException("2D image only");
	}
	if (d->get_ndim() != 1) {
		throw ImageDimensionException("1D image only");
	}

	float *dst = get_data();
	float *src = d->get_data();

	for (int i = 0; i < ny; i++) {
		dst[i * nx + n] = src[i];
	}

	update();
	EXITFUNC;
}

float& EMData::get_value_at_wrap(int x)
{
	if (x < 0) x = nx + x;
	return rdata[x];
}

float& EMData::get_value_at_wrap(int x, int y)
{
	if (x < 0) x = nx + x;
	if (y < 0) y = ny + y;
	
	return rdata[x + y * nx];
}

float& EMData::get_value_at_wrap(int x, int y, int z)
{
	int lx = x;
	int ly = y;
	int lz = z;
	if (lx < 0) lx = nx + lx;
	if (ly < 0) ly = ny + ly;
	if (lz < 0) lz = nz + lz;
	
	return rdata[lx + ly * nx + lz * nxy];
}


float EMData::get_value_at_wrap(int x) const
{
	if (x < 0) x = nx - x;
	return rdata[x];
}

float EMData::get_value_at_wrap(int x, int y) const
{
	if (x < 0) x = nx - x;
	if (y < 0) y = ny - y;
	
	return rdata[x + y * nx];
}

float EMData::get_value_at_wrap(int x, int y, int z) const
{
	int lx = x;
	int ly = y;
	int lz = z;
	if (lx < 0) lx = nx + lx;
	if (ly < 0) ly = ny + ly;
	if (lz < 0) lz = nz + lz;
	
	return rdata[lx + ly * nx + lz * nxy];
}

float EMData::sget_value_at(int x, int y, int z) const
{
	if (x < 0 || x >= nx || y < 0 || y >= ny || z < 0 || z >= nz) {
		return 0;
	}
	return rdata[x + y * nx + z * nxy];
}


float EMData::sget_value_at(int x, int y) const
{
	if (x < 0 || x >= nx || y < 0 || y >= ny) {
		return 0;
	}
	return rdata[x + y * nx];
}


float EMData::sget_value_at(size_t i) const
{
	size_t size = nx*ny;
	size *= nz;
	if (i >= size) {
		return 0;
	}
	return rdata[i];
}


float EMData::sget_value_at_interp(float xx, float yy) const
{
	int x = static_cast < int >(Util::fast_floor(xx));
	int y = static_cast < int >(Util::fast_floor(yy));

	float p1 = sget_value_at(x, y);
	float p2 = sget_value_at(x + 1, y);
	float p3 = sget_value_at(x, y + 1);
	float p4 = sget_value_at(x + 1, y + 1);
	
	float result = Util::bilinear_interpolate(p1, p2, p3, p4, xx - x, yy - y);
	return result;
}


float EMData::sget_value_at_interp(float xx, float yy, float zz) const
{
	int x = (int) Util::fast_floor(xx);
	int y = (int) Util::fast_floor(yy);
	int z = (int) Util::fast_floor(zz);

	float p1 = sget_value_at(x, y, z);
	float p2 = sget_value_at(x + 1, y, z);
	float p3 = sget_value_at(x, y + 1, z);
	float p4 = sget_value_at(x + 1, y + 1, z);

	float p5 = sget_value_at(x, y, z + 1);
	float p6 = sget_value_at(x + 1, y, z + 1);
	float p7 = sget_value_at(x, y + 1, z + 1);
	float p8 = sget_value_at(x + 1, y + 1, z + 1);

	float result = Util::trilinear_interpolate(p1, p2, p3, p4, p5, p6, p7, p8,
											   xx - x, yy - y, zz - z);

	return result;
}


EMData & EMData::operator+=(float n)
{
	add(n);
	update();
	return *this;
}


EMData & EMData::operator-=(float n)
{
	*this += (-n);
	return *this;
}


EMData & EMData::operator*=(float n)
{
	mult(n);
	update();
	return *this;
}


EMData & EMData::operator/=(float n)
{
	if (n == 0) {
		LOGERR("divided by zero");
		return *this;
	}
	*this *= (1.0f / n);
	return *this;
}


EMData & EMData::operator+=(const EMData & em)
{
	add(em);
	update();
	return *this;
}


EMData & EMData::operator-=(const EMData & em)
{
	sub(em);
	update();
	return *this;
}


EMData & EMData::operator*=(const EMData & em)
{
	mult(em);
	update();
	return *this;
}


EMData & EMData::operator/=(const EMData & em)
{
	div(em);
	update();
	return *this;
}


EMData * EMData::power(int n) const
{
	ENTERFUNC;
	
	if( n<0 ) {
		throw InvalidValueException(n, "the power of negative integer not supported.");
	}
	
	EMData * r = this->copy();
	if( n == 0 ) {
		r->to_one();
	}
	else if( n>1 ) {
		for( int i=1; i<n; i++ ) {
			*r *= *this;
		}
	}

	r->update();
	return r;
	
	EXITFUNC;
}


EMData * EMData::sqrt() const 
{
	ENTERFUNC;
	
	if (is_complex()) {
		throw ImageFormatException("real image only");
	}
	
	EMData * r = this->copy();
	float * new_data = r->get_data();
	size_t size = nxy * nz;
	for (size_t i = 0; i < size; ++i) {
		if(rdata[i] < 0) {	
			throw InvalidValueException(rdata[i], "pixel value must be non-negative for logrithm");
		}
		else {
			if(rdata[i]) {	//do nothing with pixel has value zero 
				new_data[i] = std::sqrt(rdata[i]);
			}
		}
	}
	
	r->update();
	return r;
	
	EXITFUNC;
}


EMData * EMData::log() const
{
	ENTERFUNC;
	
	if (is_complex()) {
		throw ImageFormatException("real image only");
	}
	
	EMData * r = this->copy();
	float * new_data = r->get_data();
	size_t size = nxy * nz;
	for (size_t i = 0; i < size; ++i) {
		if(rdata[i] < 0) {	
			throw InvalidValueException(rdata[i], "pixel value must be non-negative for logrithm");
		}
		else {
			if(rdata[i]) {	//do nothing with pixel has value zero 
				new_data[i] = std::log(rdata[i]);
			}
		}
	}
	
	r->update();
	return r;
	
	EXITFUNC;
}


EMData * EMData::log10() const
{
	ENTERFUNC;
	
	if (is_complex()) {
		throw ImageFormatException("real image only");
	}
	
	EMData * r = this->copy();
	float * new_data = r->get_data();
	size_t size = nxy * nz;
	for (size_t i = 0; i < size; ++i) {
		if(rdata[i] < 0) {	
			throw InvalidValueException(rdata[i], "pixel value must be non-negative for logrithm");
		}
		else {
			if(rdata[i]) {	//do nothing with pixel has value zero 
				new_data[i] = std::log10(rdata[i]);
			}
		}
	}
	
	r->update();
	return r;
	
	EXITFUNC;
}


EMData * EMData::real() const //real part has half of x dimension for a complex image
{
	ENTERFUNC;
	
	EMData * e = new EMData();

	if( is_real() ) // a real image, return a copy of itself
	{
		e = this->copy();
	}
	else //for a complex image
	{
		if( !is_ri() ) 
		{
			delete e;
			throw InvalidCallException("This image is in amplitude/phase format, this function call require a complex image in real/imaginary format.");
		}
		int nx = get_xsize();
		int ny = get_ysize();
		int nz = get_zsize();
		e->set_size(nx/2, ny, nz);
		float * edata = e->get_data();
		for( int i=0; i<nx; i++ )
		{
			for( int j=0; j<ny; j++ )
			{
				for( int k=0; k<nz; k++ )
				{
					if( i%2 == 0 )
					{
						//complex data in format [real, complex, real, complex...]
						edata[i/2+j*(nx/2)+k*(nx/2)*ny] = rdata[i+j*nx+k*nx*ny];
					}
				}
			}
		}
	}
	
	e->set_complex(false);
	if(e->get_ysize()==1 && e->get_zsize()==1) {
		e->set_complex_x(false);
	}
	e->update();
	return e;

	EXITFUNC;
}


EMData * EMData::imag() const
{
	ENTERFUNC;

	EMData * e = new EMData();

	if( is_real() ) {	//a real image has no imaginary part, throw exception
		throw InvalidCallException("No imaginary part for a real image, this function call require a complex image.");
	}
	else {	//for complex image
		if( !is_ri() ) {	
			throw InvalidCallException("This image is in amplitude/phase format, this function call require a complex image in real/imaginary format.");
		}
		int nx = get_xsize();
		int ny = get_ysize();
		int nz = get_zsize();
		e->set_size(nx/2, ny, nz);
		float * edata = e->get_data();
		for( int i=0; i<nx; i++ ) {
			for( int j=0; j<ny; j++ ) {
				for( int k=0; k<nz; k++ ) {
					if( i%2 == 1 ) {
						//complex data in format [real, complex, real, complex...]
						edata[i/2+j*(nx/2)+k*(nx/2)*ny] = rdata[i+j*nx+k*nx*ny];
					}
				}
			}
		}
	}
	
	e->set_complex(false);
	if(e->get_ysize()==1 && e->get_zsize()==1) {
		e->set_complex_x(false);
	}
	e->update();
	return e;

	EXITFUNC;
}

EMData * EMData::absi() const//abs has half of x dimension for a complex image
{
	ENTERFUNC;
	
	EMData * e = new EMData();

	if( is_real() ) // a real image
	{
		e = this->copy();
		int nx = get_xsize();
		int ny = get_ysize();
		int nz = get_zsize();
		float *edata = e->get_data();
		
		for( int i=0; i<nx; i++ ) {
			for( int j=0; j<ny; j++ ) {
				for( int k=0; k<nz; k++ ) {
					edata[i+j*nx+k*nx*ny] = std::abs(rdata[i+j*nx+k*nx*ny]);
				}
			}
		}
	}
	else //for a complex image
	{
		if( !is_ri() ) 
		{
			throw InvalidCallException("This image is in amplitude/phase format, this function call require a complex image in real/imaginary format.");
		}
		int nx = get_xsize();
		int ny = get_ysize();
		int nz = get_zsize();
		e->set_size(nx/2, ny, nz);
		float * edata = e->get_data();
		for( int i=0; i<nx; i++ )
		{
			for( int j=0; j<ny; j++ )
			{
				for( int k=0; k<nz; k++ )
				{
					if( i%2 == 0 )
					{
						//complex data in format [real, complex, real, complex...]
						edata[i/2+j*(nx/2)+k*(nx/2)*ny] =
						std::sqrt(rdata[i+j*nx+k*nx*ny]*rdata[i+j*nx+k*nx*ny]+rdata[i+1+j*nx+k*nx*ny]*rdata[i+1+j*nx+k*nx*ny]);
					}
				}
			}
		}
	}
	
	e->set_complex(false);
	if(e->get_ysize()==1 && e->get_zsize()==1) {
		e->set_complex_x(false);
	}
	e->update();
	return e;

	EXITFUNC;
}


EMData * EMData::amplitude() const
{
	ENTERFUNC;
	
	EMData * e = new EMData();
	
	if( is_real() ) {	
		throw InvalidCallException("No imaginary part for a real image, this function call require a complex image.");
	}
	else {
		if(is_ri()) {
			throw InvalidCallException("This image is in real/imaginary format, this function call require a complex image in amplitude/phase format.");
		}
		
		int nx = get_xsize();
		int ny = get_ysize();
		int nz = get_zsize();
		e->set_size(nx/2, ny, nz);
		float * edata = e->get_data();
		for( int i=0; i<nx; i++ )
		{
			for( int j=0; j<ny; j++ )
			{
				for( int k=0; k<nz; k++ )
				{
					if( i%2 == 0 )
					{
						//complex data in format [amp, phase, amp, phase...]
						edata[i/2+j*(nx/2)+k*(nx/2)*ny] = rdata[i+j*nx+k*nx*ny];
					}
				}
			}
		}
	}
	
	e->set_complex(false);
	if(e->get_ysize()==1 && e->get_zsize()==1) {
		e->set_complex_x(false);
	}
	e->update();
	return e; 	
	
	EXITFUNC;
}

EMData * EMData::phase() const
{
	ENTERFUNC;
	
	EMData * e = new EMData();
	
	if( is_real() ) {
		delete e;
		throw InvalidCallException("No imaginary part for a real image, this function call require a complex image.");
	}
	else {
		if(is_ri()) {
			delete e;
			throw InvalidCallException("This image is in real/imaginary format, this function call require a complex image in amplitude/phase format.");
		}
		
		int nx = get_xsize();
		int ny = get_ysize();
		int nz = get_zsize();
		e->set_size(nx/2, ny, nz);
		float * edata = e->get_data();
		for( int i=0; i<nx; i++ ) {
			for( int j=0; j<ny; j++ ) {
				for( int k=0; k<nz; k++ ) {
					if( i%2 == 1 ) {
						//complex data in format [real, complex, real, complex...]
						edata[i/2+j*(nx/2)+k*(nx/2)*ny] = rdata[i+j*nx+k*nx*ny];
					}
				}
			}
		}
	}
	
	e->set_complex(false);
	if(e->get_ysize()==1 && e->get_zsize()==1) {
		e->set_complex_x(false);
	}
	e->update();
	return e;
	
	EXITFUNC;
}

EMData * EMData::real2complex(const float img) const
{
	ENTERFUNC;

	if( is_complex() ) {
		throw InvalidCallException("This function call only apply to real image");
	}
	
	EMData * e = new EMData();
	int nx = get_xsize();
	int ny = get_ysize();
	int nz = get_zsize();
	e->set_size(nx*2, ny, nz);
	
	for( int k=0; k<nz; k++ ) {
		for( int j=0; j<ny; j++ ) {
			for( int i=0; i<nx; i++ ) {			
				(*e)(i*2,j,k) = (*this)(i,j,k);
				(*e)(i*2+1,j,k) = img;
			}
		}
	}
	
	e->set_complex(true);
	if(e->get_ysize()==1 && e->get_zsize()==1) {
		e->set_complex_x(true);
	}
	e->set_ri(true);
	e->update();
	return e;

	EXITFUNC;
}

void EMData::to_value(const float& value)
{
	ENTERFUNC;
	memset((void*)rdata, value, nxy*nz*sizeof(float));

	update();
	EXITFUNC;
}

void EMData::to_zero()
{
	ENTERFUNC;

	if (is_complex()) {
		set_ri(true);
	}
	else {
		set_ri(false);
	}

	memset(rdata, 0, nxy * nz * sizeof(float));
	update();
	EXITFUNC;
}

void EMData::to_one()
{
	ENTERFUNC;

	if (is_complex()) {
		set_ri(true);
	}
	else {
		set_ri(false);
	}

	for (int i = 0; i < nxy * nz; i++) {
		rdata[i] = 1.0f;
	}

	update();
	EXITFUNC;
}
