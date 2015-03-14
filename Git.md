# Introduction #

Git is a distributed version control system. It's in much times faster and flexible one than SVN, therefore it's used for PyICQt development now.


# Details #

Do you want to get updates directly from git repo?
It's not a problem.

**Branches**

unstable - main branch for testing

master - latest stable version (currently _0.8.1_). Recommended for use.

oldstable - previous stable version (currently _0.8_).

**Initial actions**

First, clone repo and put its content in _pyicqt_ folder, for example:
```
git clone git://gitorious.org/pyicqt/mainline.git pyicqt
```

Ok, you have full copy of PyICQt. Let's enter in just created folder
```
cd pyicqt
```

Jump to _update_ section if you want to use only stable version. In other case read next.

Now you should select separate branch, which is necessary for you:
```
git branch --track unstable origin/unstable
```

After this initial clone you track _unstable_ branch.

For switching from one branch to other (_unstable_ here) type:
```
git checkout unstable
```

**Update**

You should run only one command to update PyICQt:
```
git pull
```

That's all. Enjoy!