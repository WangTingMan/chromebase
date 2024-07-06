#ifndef GTEST_PROD_H__
#define GTEST_PROD_H__

#include <build/build_config.h>

#ifdef GTEST_DISABLED
#ifndef FRIEND_TEST
#define FRIEND_TEST( A, B )
#endif
#else
#include <gtest/gtest_prod.h>
#endif

#endif
