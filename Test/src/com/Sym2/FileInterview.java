package com.Sym2;

import java.io.File;
import java.util.List;
import java.util.Stack;

public class FileInterview {
/*	C:\Windows
	/root

	===> Every dir list and files in it
	Directory Crawler
	C:\Windows\Sys32 
	C:\Windows\Sys32 \\ blah.txt*/

	Stack s = new Stack();
	void directoryListing(String path){
	    File f = new File(path);
	    File[] list = f.listFiles();
		for (File newFile : list) {
			if (newFile.isDirectory()) {
				s.push(newFile.getPath());
			} else {
				sysout(newFile.getName());
			}
		}
	        String direcPath = (String) s.pop();
	        if (null != direcPath) {
		        sysout(direcPath);
		        directoryListing(direcPath);
	        }
	}
}
