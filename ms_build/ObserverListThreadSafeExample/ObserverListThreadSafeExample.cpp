#include <iostream>
#include <functional>

#include <base\system_monitor\system_monitor.h>
#include <base\message_loop\message_loop.h>
#include <base\observer_list_threadsafe.h>
#include <base\memory\scoped_refptr.h>

void Foo()
{
    std::cout << "Foo notified!\n";
}

int main()
{
    base::MessageLoop msgLoop;
    base::RunLoop loop;

    std::function<void( int, std::string )> fun = []( int x, std::string str )
    {
        std::cout << "here! " << x << " " << str << std::endl;
    };

    scoped_refptr<base::ObserverListThreadSafe<std::function<void( int, std::string )>>> list1
    ( new base::ObserverListThreadSafe<std::function<void( int, std::string )>>() );
    list1->AddObserver( &fun );

    scoped_refptr<base::ObserverListThreadSafe<decltype( Foo )>> list2
    ( new base::ObserverListThreadSafe<decltype( Foo )>() );
    list2->AddObserver( &Foo );

    list1->Notify( FROM_HERE, 23, "123" );
    list1->Notify( FROM_HERE );
    list2->Notify( FROM_HERE );
    loop.Run();
}