/**
 * 
 */
package com.study;

import java.math.MathContext;
import java.util.Date;
import java.util.TreeSet;


/**
 * @author govind.gupta
 *
 */
public class PersistentTest_Q19 /*implements Comparable<PersistentTest_Q19>*/ {
//	private synchronized String a;
	private String a;
	
	public PersistentTest_Q19(){
		this.a = this.a+1;
	}
	
	public void test(){
		synchronized (a) {
			
		}
	}
	
	public synchronized void book(){
		
	}
	
	public static void main(String[] args) {
//		System.out.println("ja"+(new String('v')));
		TreeSet<PersistentTest_Q19> ts = new TreeSet<PersistentTest_Q19>();
		ts.add(new PersistentTest_Q19());
		ts.add(new PersistentTest_Q19());
		ts.add(new PersistentTest_Q19());
		System.out.println(ts.last());
		
		/*TreeSet<String> ts1 = new TreeSet<String>();
		ts1.add(new String());
		ts1.add(new String());
		ts1.add(new String());
		System.out.println(ts1.last());
		StringBuffer sb = new StringBuffer();
		Date d = new Date();*/
	}
	
	/*@Override
	public int compareTo(PersistentTest_Q19 pt)
	{
		return a.compareTo(pt.a);
	}*/

/*	@Override
	public int compareTo(Object arg0) {
		a.compareTo(arg0.a);
	}*/
}

