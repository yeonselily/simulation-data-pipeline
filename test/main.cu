#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <vector>

#include <gtest/gtest.h>
#include <mass/Mass.h>

TEST(AppTemplate, Test) {
    mass::Mass::init();
    mass::Mass::finish();
    
    ASSERT_TRUE(true);
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);

    return RUN_ALL_TESTS();
}
