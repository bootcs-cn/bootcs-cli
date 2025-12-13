#include <stdio.h>

int main(void)
{
    int cents;
    
    // 获取有效输入
    do
    {
        printf("Change owed: ");
        scanf("%d", &cents);
    }
    while (cents < 0);
    
    int coins = 0;
    
    // 25 美分
    coins += cents / 25;
    cents %= 25;
    
    // 10 美分
    coins += cents / 10;
    cents %= 10;
    
    // 5 美分
    coins += cents / 5;
    cents %= 5;
    
    // 1 美分
    coins += cents;
    
    printf("%d\n", coins);
    
    return 0;
}
