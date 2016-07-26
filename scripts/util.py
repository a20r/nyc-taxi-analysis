
import time


def profile(pargs=True):
    def dec(f):
        def __inner(*args, **kwargs):
            very_big = 1000
            print "Executing:", f.func_name
            if pargs:
                print "With Args:",
                arg_str = str()
                for i, v in enumerate(f.func_code.co_varnames[:len(args)]):
                    astr = repr(args[i])
                    if len(astr) > very_big:
                        astr = str(type(args[i]))
                    arg_str += "\n\t" + str(v) + ":" + astr
                if len(arg_str) == 0:
                    print "None"
                else:
                    print arg_str
                print "With Kwargs:",
                if len(kwargs.keys()) > 0:
                    print ""
                    for key in kwargs:
                        kwstr = repr(kwargs[key])
                        if len(kwstr) > very_big:
                            kwstr = type(kwargs[key])
                        print "\t", key, ":", kwstr
                else:
                    print "None"
            start = time.time()
            res = f(*args, **kwargs)
            end = time.time()
            print "Result:", repr(res) if len(repr(res)) < 1000 else type(res)
            print "Execution Duration:", end - start, "seconds\n"
            return res
        return __inner
    return dec
