package com.programming.array;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;
import java.util.TreeSet;

public class StringPermutation {

	public static void main(String[] args) {
		String permStr = "abca";
		Set<String> out = permutations(permStr);
		for(String o : out)
		{
			System.out.println(o);
		}
	}
	
	static void permute(String permStr){
		TreeSet<String> permSet = new TreeSet<String>();
		for(int i=0;i<permStr.length();i++)
		{
			permSet.add(String.valueOf(permStr.charAt(i)));
		}
		String[] combi = (String[]) permSet.toArray();
		for (int i=0;i<combi.length;i++)
		{
			
		}
	}
	

	public static Set<String> permutations(String s) {
		Set<String> out = new HashSet<String>();
		if (s.length() == 1) {
			out.add(s);
			return out;
		}
		char first = s.charAt(0);
		String rest = s.substring(1);
		for (String permutation : permutations(rest)) {
			out.addAll(insertAtAllPositions(first, permutation));
		}
		return out;
	}

	public static Set<String> insertAtAllPositions(char ch, String s) {
		Set<String> out = new HashSet<String>();
		for (int i = 0; i <= s.length(); ++i) {
			String inserted = s.substring(0, i) + ch + s.substring(i);
			out.add(inserted);
		}
		return out;
	}


}
