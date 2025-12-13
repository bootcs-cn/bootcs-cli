#include <stdio.h>

int main(void)
{
    int height;
    
    // 获取有效高度 (1-8)
    do
    {
        printf("Height: ");
        scanf("%d", &height);
    }
    while (height < 1 || height > 8);
    
    // 打印金字塔
    for (int i = 1; i <= height; i++)
    {
        // 打印空格
        for (int j = 0; j < height - i; j++)
        {
            printf(" ");
        }
        // 打印 #
        for (int j = 0; j < i; j++)
        {
            printf("#");
        }
        printf("\n");
    }
    
    return 0;
}
