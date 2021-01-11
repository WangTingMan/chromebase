#include <iostream>
#include <base/debug/stack_trace.h>

void TestFoo()
{
    base::debug::StackTrace trace;
    std::string callStack = trace.ToString();
    std::cout << "The call stack is:\n" << callStack;
}

void InvokeFoo()
{
    TestFoo();
}

int main()
{
    InvokeFoo();
    std::cout << "Hello World!\n";
}
