/**
 * 
 */
package com.study;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * @author govind.gupta
 *
 */
public class PersistentTest_Q6 {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Set<Integer> set = new LinkedHashSet<Integer>();
		List<Integer> list = new ArrayList<Integer>();
		for(int i=-3; i<3;i++)
		{
			set.add(i);
			list.add(i);
		}
		for(int i=0; i<3;i++)
		{
			set.remove(i);
			list.remove(i);
			System.out.println(set + " : "+list);
		}
		System.out.println(set + " : "+list);
	}
}
