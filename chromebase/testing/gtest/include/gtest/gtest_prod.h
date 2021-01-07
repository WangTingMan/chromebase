#ifndef GTEST_PROD_H__
#define GTEST_PROD_H__

#ifdef GTEST_DISABLED
#define FRIEND_TEST( A, B ) 
#else
#include <gtest/gtest_prod.h>
#endif

#endif
