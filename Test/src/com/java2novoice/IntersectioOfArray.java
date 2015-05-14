package com.java2novoice;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public class IntersectioOfArray {

	public static void main(String[] args) {
		int[] a = {5, 3, 10, 70, 1, -2, -6};
		int[] b = {4, 3, -6, 2};
		printIntersectionOfArray(a, b);
	}

	
	static void printIntersectionOfArray(int[] a, int[] b){
		Map<Integer, Integer> intersectMap = new HashMap<>();
		int i=0;
		for(;;i++){
			if (i < a.length)
			{
				if (intersectMap.containsKey(a[i])){
					intersectMap.put(a[i], intersectMap.get(a[i])+1);
				}
				else{
					intersectMap.put(a[i], 1);
				}
			}
			if (i < b.length)
			{
				if (intersectMap.containsKey(b[i])){
					intersectMap.put(b[i], intersectMap.get(b[i])+1);
				}
				else{
					intersectMap.put(b[i], 1);
				}
			}
			if(i >= a.length && i >= b.length){
				break;
			}
		}
		Set<Integer> set = intersectMap.keySet();
		for(Integer ele : set){
			if(intersectMap.get(ele) > 1){
				System.out.println("intersectedElement : "+ele);
			}
		}
	}
}
